#########################################################################
# Search Trajectory Networks (STNs)
# for Multi-Objective Evolutionary Algorithms in Combinatorial Optimisation
# Gabriela Ochoa,  Arnaud Liefhooghe,  Yuri Lavinas, Claus Aranha
# January 2023
# STN construction
# Input:  Text file with trajectory data of several runs
# Output: STN graph objects saved in RData files
#########################################################################
rm(list = ls(all = TRUE))
library(igraph)
library(tidyr)
library(dplyr)


nGen <-  20  # number of algorithm iterations/generations 
nRun <-  10   # Number of runs to consider
dec <-  6   # Number of decimal digits for fitness (Pareto set) 

infolder <- "data/mowflop_x80/"      # Base folder with data 
parfolder <- "pf/mowflop/"          # Folder with Pareto front objective values
outfolder <- "stns/mowflop_x80/"  # Base folder to save STNs

isets<- c("MOEAD/","NSGA2/") # folders with sets data to process

bpf_col_types <- c("numeric", "numeric")  # Base Column types for Pareto front

bdf_col_types <-  c("numeric", "numeric", "character", "character", # Base Columns for trajectory data
          "integer", "integer","character", "character", "character")

# -----------------------------------------------------------------------------
#  Function to Join the names of the non-null vectors
#  Receives the columns of the data frame to join
#  Returns the vector of concatenated column names
#-----------------------------------------------------------------------------
join_vectors = function(x)
{
   ans = character(nrow(x))
   for(j in seq_along(x)) {
      i = x[[j]] > 0L
      ans[i] = paste(ans[i], names(x)[[j]], sep = "_")
   }
   return(gsub("^_", "", ans))
}

# -----------------------------------------------------------------------------
# Create a STN object from the input data
# The input file contains several runs 
# A RData file is saved containing the STN and the nodes and edges dataframes
#-----------------------------------------------------------------------------

# iset <- isets[2]
# fname <-  paste0(infolder, iset)
# data_files <- list.files(fname)  # filenames
# instance <- data_files[3]

create_stn = function(instance, iset) {
   # Extract name for Pareto front file
   aux <- strsplit(instance, "_")[[1]]  # Decompose the name to take Pareto set
   pfname <- paste(aux[2],aux[3],aux[4],aux[5],aux[6],aux[7],sep="_")
   pfname <- paste0(parfolder, pfname, "_ref.txt")
   fname <- paste0(infolder,iset, instance)
   m <- as.integer(aux[4])
   # Read Pareto set and trajectory data - for m = 2 and 3 objectives
   if (m == 2) {   # two objectives 
      pf_col_types <- bpf_col_types
      pf_col_names <- c("f1", "f2")
      df_col_types <- bdf_col_types
   } else {  # 3 Objectives:  one numeric to col types
      pf_col_types <- c("numeric",bpf_col_types)
      pf_col_names <-c("f1", "f2", "f3")
      df_col_types <- c("numeric", bdf_col_types)
   }   
   
   # Read Pareto Front
   print("Pareto: ")
   print(pfname)
   pf <- read.table(pfname, stringsAsFactors = F,  colClasses = pf_col_types)
   colnames(pf) <- pf_col_names
   # Read trajectory data
   print("Trajectory: ")
   print(fname)
   df <- read.table(fname, stringsAsFactors = F, header = T,
                    colClasses=df_col_types)

   # MoWFLOP patch: nGen/nRun are overridden here, per file, instead of
   # using the global constants at the top of the script. STN_MoWFLOP
   # samples every STN_LOGGER_INTERVAL generations instead of logging
   # every one, and different runs in the same file can reach different
   # final generations within the same evaluation budget -- a fixed nGen
   # can end up smaller than some run's actual final generation, which
   # leaves an edge's target node out of `nodes` and breaks
   # graph_from_data_frame() further down ("Some vertex names in `d` are
   # not listed in `vertices`").
   nGen <- max(df$Gen) + 1
   nRun <- max(df$Run)

   # Data structure to keep name of vectors - Depends on the number of Objectives!
   if (m == 2) {
      wei <- select(df, Vector:Weight2)
      wei <- wei[!duplicated(wei), ]   # Remove duplicates
      wei$label <- paste0("(", wei$Weight1, ", ", wei$Weight2, ")")
   } else {
      wei <- select(df, Vector:Weight3)
      wei <- wei[!duplicated(wei), ]   # Remove duplicates
      wei$label <- paste0("(", wei$Weight1, ",", wei$Weight2, ",", wei$Weight3, ")")
   }
   nVec <- nrow(wei)  # Number of distinct vectors
   # Named vector that can be useful for plot labels
   weiv <- wei$label
   names(weiv) <- wei$Vector
   # Filter Relevant rows
   df <- filter(df, Gen <= nGen, Run <= nRun)
   # Select relevant columns
   df <- select(df,f1:Vector)
   
   
   #------------------------------------------------------------------------------
   #  Creation of the nodes dataframe 
   #------------------------------------------------------------------------------
   
   # Get the start and end nodes of trajectories.
   start <- df %>%
      filter (df$Gen == 0)
   
   # MoWFLOP patch: the original "end" compared against a single nGen for
   # the whole file -- in MOEA/D, crossover/mutation are probabilistic per
   # generation (see moead.cpp), so different runs sharing the same
   # evaluation budget end at different final generations. A global nGen
   # only captured the run that went furthest, missing the final node of
   # every shorter run (the n_end metric would come out incomplete/wrong).
   # Instead, take each run's own last logged generation individually.
   end <- df %>%
      group_by(Run) %>%
      filter(Gen == max(Gen)) %>%
      ungroup()
   #  Aggregate rows and count the number of solutions for each vector.
   
   if (m == 2) {
   s <- df %>%
      group_by(f1,f2,Solution1, Vector) %>%
      summarise(Count = n())
   } else {  # 3 Objectives
      s <- df %>%
         group_by(f1,f2,f3,Solution1, Vector) %>%
         summarise(Count = n())
   }
   
   # Convert from long to wide, keeping a column for each Vector.
   # Fill in missing values with zero
   nodes <- s %>%
      pivot_wider(names_from = Vector, values_from = Count, values_fill = 0)
   
   # Create new relevant additional columns to nodes dataset
   # - Position: indicates position of nodes: Begin, Medium, End, Pareto
   # - Count: Number of times node was visitied by any vecotr
   # - Vectors: Contains an concatanation of the vectors that visite dde nodes.
   
   #  The Vector Columns are temporary. Keep the sum and their concatenation 
   i <- m + 2    # index of the first vector column
   j <- i + nVec -1 # Index of the last vector column
   
   vs <- nodes[, c(i:j)]  # Create dataframe with only the vector columns to join vectors
   nodes <- select(nodes,f1:Solution1)  # Remove the vector Columns
   nodes$Count <- rowSums(vs)  # Number of times nodes visited
   nodes$Position = "Medium"
   nodes$Vectors <- join_vectors(vs)
   
   nodes <- relocate(nodes, Solution1)  # Solution 1 is the first column
   nodes <- rename(nodes, Solution = Solution1)
   
   # Create column for Pareto both in the nodes df and the Pareto df
   #
   # MoWFLOP patch: the original did as.integer(round(x,dec)*10^dec) --
   # correct for her benchmark's small normalized objective values
   # (~0.4-0.7), but MoWFLOP uses raw-scale f_cost/f_power (~1e7), and
   # *10^dec overflows R's 32-bit integer range (~2.1e9), silently turning
   # into NA for everyone -- and since NA_NA == NA_NA, EVERY node was
   # getting tagged Position="Pareto". Replaced with sprintf at `dec` fixed
   # decimal places: same comparison semantics (round, then compare as a
   # string), without the integer overflow.
   dec_fmt <- paste0("%.", dec, "f")
   if (m == 2) {   # two objectives
      pf_str <- paste(sprintf(dec_fmt, pf$f1),
                      sprintf(dec_fmt, pf$f2), sep = "_")
      nobj_str <- paste(sprintf(dec_fmt, nodes$f1),
                      sprintf(dec_fmt, nodes$f2), sep = "_")
   } else {  # 3 Objectives:  one numeric to col types
      pf_str <- paste(sprintf(dec_fmt, pf$f1),
                      sprintf(dec_fmt, pf$f2),
                      sprintf(dec_fmt, pf$f3), sep = "_")
      nobj_str <- paste(sprintf(dec_fmt, nodes$f1),
                        sprintf(dec_fmt, nodes$f2),
                        sprintf(dec_fmt, nodes$f3), sep = "_")
   }
   nodes$Obj <- nobj_str
   
   # Assign Position of nodes -- There are 4 possible values
   # Begin, End, Medium, Pareto - Default is Medium
   nodes[nodes$Solution %in% start$Solution1, ]$Position = "Begin"
   nodes[nodes$Solution %in% end$Solution1, ]$Position = "End"
   # Check if objective vector is in the Pareto front
   nodes[nodes$Obj %in% pf_str, ]$Position = "Pareto"
   print("Pareto Nodes:")
   print(which(nodes$Obj %in% pf_str))
   
   #------------------------------------------------------------------------------
   #  Creation of the edges dataframe 
   #------------------------------------------------------------------------------
   
   # Discard the last generation for edges creation
   
   df <- df %>%
      filter(Gen < nGen)
   
   #  Aggregate rows and count the number of edges (sol1 -> sol2) for each vector.
   
   se <- df %>%
      group_by(Solution1, Solution2, Vector) %>%
      summarise(Count = n())
   
   # Convert from long to wide, keeping a column for each Vector.
   # Fill in missing values with zero
   edges <- se %>%
      pivot_wider(names_from = Vector, values_from = Count, values_fill = 0)
   
   # Create new relevant additional columns to edges dataset
   # - Count: Number of times node was visitied by any vecotr
   # - Vectors: Contains an concatanation of the vectors that visite dde nodes.
   # The i, j indexes for vectors are not depending of hte objectives
   i = 3
   j = i + nVec -1
   
   vs <- edges[, c(i:j)]  # Create dataframe with only the vector columns to join vectors
   edges <- select(edges, Solution1, Solution2)
   edges$Count <- rowSums(vs)  # Number of times nodes visited
   edges$Vectors <- join_vectors(vs)

   
   #------------------------------------------------------------------------------
   #  Creation the STN model from the nodes and edges dataframe
   #------------------------------------------------------------------------------
   STN<- graph_from_data_frame(edges, directed=TRUE, vertices=nodes)
   
   # Saving the STN object, but also the nodes and edges
   # As they can be useful to compute  metrics
   
   aux <- substr(instance,1,nchar(instance)-4)
   fname <- paste0(outfolder, iset, aux, ".RData")
   print(fname)
   # MoWFLOP patch: nRun (computed above from max(df$Run), per-file for the
   # same reason as nGen) used to be discarded here. par_strength (paper's
   # STN metrics table, normalized by #execucoes x p) needs the actual
   # execution count without re-reading the raw logs and without assuming
   # every file has exactly the planned 10 runs, so persist it.
   save(pf, weiv, nodes, edges, STN, nRun, file = fname)
   return (nrow(nodes))  # Return  number of nodes, just to check it
}

# ---- Get all files in the given input folder and process  -----------------------------

for (s in isets) {
   fname <-  paste0(infolder, s)
   data_files <- list.files(fname)  # filenames in folder
   # Create STNs for all files in the folder
   nnodes <- lapply(data_files, create_stn, iset = s)
   # Plot number of nodes as check
   barplot(as.numeric(unlist(nnodes)))
}




