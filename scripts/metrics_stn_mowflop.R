#########################################################################
# Search Trajectory Networks (STNs) for the MoWFLOP
# Computing the metrics table of references/STN_MoWFLOP.pdf S8
# (nodes, disc_rate, edge_ratio, shared_vec, pareto, par_strength, n_end,
#  path_par -- one STN at a time; shared_alg is computed separately by
#  shared_alg.R, since it needs a pair of files, not one)
# Input:  STN graph objects produced by `create .R` (nodes/edges/STN/weiv/nRun)
# Output: csv file with metrics
#########################################################################
rm(list = ls(all = TRUE))

library(igraph)

iset <- "mowflop_x80"  # Indicate instance set to use (folder under stns/)
algo <- "MOEAD"         # Indicate algorithm

infolder <- paste0("stns/", iset, "/", algo, "/")  # path for algorithm
outfolder <- "metrics/"

#--------------------------------------------------------------------------
# Create dataframe with metrics
# ------ Identification columns, parsed from the MoWFLOP filename
# convention, e.g. MOEAD_mowflop_ns465_2_x80_p50i50_0_post.RData:
#   t[1]=algo t[3]=instance t[5]=tag t[6]=p<P>i<iterations>
# (metrics.R's rho-mnk parsing of t[3]/t[6] as r/k does not apply here --
# see run_metrics_r.py's docstring)
# ------ Metrics (references/STN_MoWFLOP.pdf S8) ------------------------
# nodes:        |N|, total number of nodes
# disc_rate:    |N|/B, B = sum(nodes$Count) = total logged trajectory steps
# edge_ratio:   |E|/|N|
# shared_vec:   fraction of nodes visited by more than one observer vector
# pareto:       |Npar|, nodes reaching the reference Pareto set
# par_strength: sum of incoming strength of Npar nodes, normalised by
#               (#execucoes x p)
# n_end:        fraction of nodes that are trajectory endpoints outside Npar
#               (Position == "End": create .R overwrites End with Pareto
#               when both apply, so "End" already excludes Npar)
# path_par:     median shortest-path length from start nodes to Npar
#-------------------------------------------------------------------------

col_types = c("character", "character", "character", "integer",
              "integer", "numeric", "numeric", "numeric",
              "integer", "numeric", "numeric", "numeric")

col_names = c("instance", "tag", "algo", "p",
              "nodes", "disc_rate", "edge_ratio", "shared_vec",
              "pareto", "par_strength", "n_end", "path_par")

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

   n <- nrow(nodes)  # number of nodes
   nVec <- length(weiv)  # number of observer vectors
   metrics[i, "nodes"] <- n
   metrics[i, "disc_rate"] <- round(n / sum(nodes$Count), 4)

   e <- nrow(edges)  # number of edges
   metrics[i, "edge_ratio"] <- round(e / n, 4)

   metrics[i, "shared_vec"] <- round(mean(grepl("_", nodes$Vectors)), 4)

   pn <- which(V(STN)$Position == "Pareto")  # Pareto node ids
   metrics[i, "pareto"] <- length(pn)
   par_str <- sum(strength(STN, vids = pn, mode = "in"))
   metrics[i, "par_strength"] <- round(par_str / (nRun * nVec), 4)

   metrics[i, "n_end"] <- round(length(which(nodes$Position == "End")) / n, 4)

   sn <- which(V(STN)$Position == "Begin")  # Start node ids
   dg <- distances(STN, v = sn, to = pn, mode = "out", weights = NULL)
   d <- dg[is.finite(dg)]  # Remove Inf values from distance matrix d
   metrics[i, "path_par"] <- round(median(d), 4)

   i = i + 1
}

# Save metrics as .csv file
fname <- paste0(outfolder, iset, "_", algo, "_stn_metrics.csv")
write.csv(metrics, fname, row.names = FALSE)
