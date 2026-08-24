#########################################################################
# Search Trajectory Networks (STNs) for the MoWFLOP
# Computing shared_alg (references/STN_MoWFLOP.pdf S8): the fraction of
# locations visited by more than one algorithm.
#
# This does NOT merge MOEAD's and NSGA2's STNs into one graph.
# Instead this compares the two algorithms' node-id *sets* directly:
# node ids (nodes$Solution, aka the location id assigned
# by scripts/mowflop/schemes.py) are a deterministic hash of the visited
# location's content, built once per (instance, config) from the combined
# MOEAD+NSGA2 raw log (see partition.py:run_one), so the same location
# gets the same id in both algorithms' .RData regardless of which one
# visited it. That is what makes a plain set intersection valid here.
#
# Input:  STN graph objects produced by `create .R`, one folder per algo
# Output: csv file with shared_alg per (instance, p-config)
#########################################################################
rm(list = ls(all = TRUE))

iset <- "mowflop_x80"  # Indicate instance set to use (folder under stns/)

moead_folder <- paste0("stns/", iset, "/MOEAD/")
nsga2_folder <- paste0("stns/", iset, "/NSGA2/")
outfolder <- "metrics/"

#--------------------------------------------------------------------------
# Pair files across the two algorithm folders by their shared suffix
# (everything after the "<ALGO>_" prefix, e.g.
# "mowflop_ns465_2_x80_p50i50_0_post.RData" pairs
# "MOEAD_mowflop_ns465_..." with "NSGA2_mowflop_ns465_...").
# Pairs missing one of the two algorithms are skipped.
#--------------------------------------------------------------------------

suffix_of <- function(fname) sub("^[^_]+_", "", fname)

moead_files <- list.files(moead_folder)
nsga2_files <- list.files(nsga2_folder)

moead_by_suffix <- setNames(moead_files, suffix_of(moead_files))
nsga2_by_suffix <- setNames(nsga2_files, suffix_of(nsga2_files))

common_suffixes <- intersect(names(moead_by_suffix), names(nsga2_by_suffix))
missing <- union(
   setdiff(names(moead_by_suffix), names(nsga2_by_suffix)),
   setdiff(names(nsga2_by_suffix), names(moead_by_suffix))
)
if (length(missing) > 0) {
   cat("skipping (missing one algorithm):\n")
   print(missing)
}

col_types = c("character", "character", "integer",
              "numeric", "integer", "integer", "integer")
col_names = c("instance", "tag", "p",
              "shared_alg", "n_moead", "n_nsga2", "n_union")
metrics <- read.table(text = "", colClasses = col_types, col.names = col_names)

i = 1
for (suffix in common_suffixes) {
   moead_file <- moead_by_suffix[[suffix]]
   nsga2_file <- nsga2_by_suffix[[suffix]]
   print(suffix)

   load(paste0(moead_folder, moead_file), verbose = F)
   moead_solutions <- nodes$Solution
   load(paste0(nsga2_folder, nsga2_file), verbose = F)
   nsga2_solutions <- nodes$Solution

   t <- strsplit(suffix, "_")[[1]]  # suffix starts at "mowflop_<instance>_..."
   metrics[i, "instance"] <- t[2]
   metrics[i, "tag"] <- t[4]
   p_match <- regmatches(t[5], regexpr("(?<=p)[0-9]+", t[5], perl = TRUE))
   metrics[i, "p"] <- as.integer(p_match)

   n_moead <- length(unique(moead_solutions))
   n_nsga2 <- length(unique(nsga2_solutions))
   n_shared <- length(intersect(moead_solutions, nsga2_solutions))
   n_union <- length(union(moead_solutions, nsga2_solutions))

   metrics[i, "n_moead"] <- n_moead
   metrics[i, "n_nsga2"] <- n_nsga2
   metrics[i, "n_union"] <- n_union
   metrics[i, "shared_alg"] <- round(n_shared / n_union, 4)

   i = i + 1
}

# Save metrics as .csv file
fname <- paste0(outfolder, iset, "_shared_alg.csv")
write.csv(metrics, fname, row.names = FALSE)
