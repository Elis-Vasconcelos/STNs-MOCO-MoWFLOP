#########################################################################
# Search Trajectory Networks (STNs) for the MoWFLOP
# Computing the STN metrics table for the MoWFLOP
# (nodes, disc_rate, edge_ratio, shared_vec, pareto, par_strength,
#  n_end, path_par -- one STN at a time; shared_alg is computed separately
#  by shared_alg.R, since it needs a pair of files)
# Input:  STN graph objects produced by `create .R` (nodes/edges/STN/weiv/nRun),
#         plus the raw trajectory log each one was built from (par_strength)
# Output: csv file with metrics
#########################################################################
rm(list = ls(all = TRUE))

library(igraph)

iset <- "mowflop_x80"  # Indicate instance set to use (folder under stns/)
algo <- "MOEAD"         # Indicate algorithm

infolder <- paste0("stns/", iset, "/", algo, "/")  # path for algorithm
datafolder <- paste0("data/", iset, "/", algo, "/")  # raw logs, same names
outfolder <- "metrics/"

#--------------------------------------------------------------------------
# Create dataframe with metrics
# ------ Identification columns, parsed from the MoWFLOP filename
# convention, e.g. MOEAD_mowflop_ns465_2_x80_p50i50_0_post.RData:
#   t[1]=algo t[3]=instance t[5]=tag t[6]=p<P>i<iterations>
# (metrics.R's rho-mnk parsing of t[3]/t[6] as r/k does not apply here --
# see run_metrics_r.py's docstring)
#   t[7]=run label: "0" for aggregated datasets, "r<NN>" for one wind scenario
# ------ Metrics, each definition spelled out below
# nodes:        |N|, total number of nodes
# disc_rate:    |N|/B, B = sum(nodes$Count) = total logged trajectory steps
# edge_ratio:   |E|/|N|
# shared_vec:   fraction of nodes visited by more than one observer vector
# pareto:       |Npar|, nodes reaching the reference Pareto set
# par_strength: fraction of trajectories that reach Npar -- each (Run, Vector)
#               pair counts 1 if any of its logged locations is a Pareto node
#               (passing through or ending there), 0 otherwise, divided by the
#               number of trajectories (#execucoes x p). Lies in [0, 1] by
#               construction. The advisor's definition, replacing the literal
#               sum of weighted s_in over Npar, which grew past 1 with the
#               attractor's self-loop weight (ns465 p100: 6.95)
#               The .RData cannot give this in aggregated files: nodes record
#               which vectors visited them but not in which run, so V3 of run
#               1 and V3 of run 5 merge (union of vectors gives 0.99 where the
#               true fraction is 0.488 -- ns101 p100 MOEA/D). The raw log with
#               the same name under data/ is read instead
# #execucoes: 1 in per-run files -- create .R's nRun is max(df$Run), which is
#               r+1 in a file holding only run r
# n_end:        fraction of nodes that are trajectory endpoints outside Npar
#               (Position == "End": create .R overwrites End with Pareto
#               when both apply, so "End" already excludes Npar)
# path_par:     med_{v0} d(v0, Npar), d(v0, Npar) = min over Npar of the
#               shortest-path length, median over the start nodes that
#               reach Npar. A start node that is also End/Pareto lost its
#               "Begin" label in create .R and is left out (rare)
# path_par_reach: fraction of start nodes with a finite d(v0, Npar)
#-------------------------------------------------------------------------

col_types = c("character", "character", "character", "integer", "character",
              "integer", "numeric", "numeric", "numeric",
              "integer", "numeric", "numeric", "numeric", "numeric")

col_names = c("instance", "tag", "algo", "p", "run",
              "nodes", "disc_rate", "edge_ratio", "shared_vec",
              "pareto", "par_strength", "n_end",
              "path_par", "path_par_reach")

metrics <- read.table(text = "", colClasses = col_types, col.names = col_names)

# ---- Get all files in the given input folder -----------------------------

data_files <- list.files(infolder)  # filenames in folder

i = 1    # index to store in dataframe
for (instance in data_files) {
   print(instance)
   load(paste0(infolder, instance), verbose = F)
   t <- strsplit(instance, "_")[[1]]
   metrics[i, "instance"] <- t[3]
   metrics[i, "tag"] <- t[5]
   metrics[i, "algo"] <- t[1]
   p_match <- regmatches(t[6], regexpr("(?<=p)[0-9]+", t[6], perl = TRUE))
   metrics[i, "p"] <- as.integer(p_match)
   metrics[i, "run"] <- t[7]
   n_exec <- if (grepl("^r[0-9]+$", t[7])) 1L else nRun  # executions in this file

   n <- nrow(nodes)  # number of nodes
   nVec <- length(weiv)  # number of observer vectors
   metrics[i, "nodes"] <- n
  
   # qtd de nós / soma da qtd de vezes que cada nó foi visitado
   metrics[i, "disc_rate"] <- round(n / sum(nodes$Count), 4)

   e <- nrow(edges)  # number of edges
   metrics[i, "edge_ratio"] <- round(e / n, 4)

   # a coluna Vectors .RData guarda os vetores que visitaram aquele nó separados por "_", então média dos que tem "_" é a fração de nós visitados por mais de um vetor
   metrics[i, "shared_vec"] <- round(mean(grepl("_", nodes$Vectors)), 4)

   pn <- which(V(STN)$Position == "Pareto")  # Qtd de nós com rótulo Pareto
   metrics[i, "pareto"] <- length(pn)
   # Solution1 covers every logged location of a trajectory, the last one
   # included (create .R requires every Solution2 to appear as a Solution1)
   rawname <- paste0(datafolder, sub("\\.RData$", ".txt", instance))
   if (file.exists(rawname)) {
      raw <- read.table(rawname, header = T, colClasses = "character")
      raw <- raw[, c("Solution1", "Run", "Vector")]
      par_ids <- V(STN)$name[pn]
      traj <- unique(raw[, c("Run", "Vector")])  # one row per trajectory
      hit <- unique(raw[raw$Solution1 %in% par_ids, c("Run", "Vector")])
      if (nrow(traj) != n_exec * nVec) {
         message("warning: ", instance, ": ", nrow(traj), " trajectories in ",
                 "the raw log, expected ", n_exec * nVec, " (#execucoes x p)")
      }
      metrics[i, "par_strength"] <- round(nrow(hit) / nrow(traj), 4)
   } else {
      message("warning: ", instance, ": raw log not found (", rawname,
              "), par_strength = NA")
      metrics[i, "par_strength"] <- NA
   }

   metrics[i, "n_end"] <- round(length(which(nodes$Position == "End")) / n, 4)

   sn <- which(V(STN)$Position == "Begin")  # Start node ids
   if (length(sn) > 0 && length(pn) > 0) {
      dg <- distances(STN, v = sn, to = pn, mode = "out", weights = NULL)
      dmin <- apply(dg, 1, min)  # d(v0, Npar): nearest Pareto node per start
      reach <- is.finite(dmin)
      metrics[i, "path_par"] <- if (any(reach)) round(median(dmin[reach]), 4) else NA
      metrics[i, "path_par_reach"] <- round(mean(reach), 4)
   } else {
      metrics[i, "path_par"] <- NA
      metrics[i, "path_par_reach"] <- if (length(sn) > 0) 0 else NA
   }

   i = i + 1
}

# Save metrics as .csv file
fname <- paste0(outfolder, iset, "_", algo, "_stn_metrics.csv")
write.csv(metrics, fname, row.names = FALSE)
