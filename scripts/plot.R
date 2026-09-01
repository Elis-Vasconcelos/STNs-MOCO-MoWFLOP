#########################################################################
# STNs- MOCO: Search Trajectory Networks (STNs)
# for Multi-Objective Evolutionary Algorithms in Combinatorial Optimisation
# Gabriela Ochoa,  Arnaud Liefhooghe,  Yuri Lavinas, Claus Aranha
# January 2023
# STN Visualisation  
# Input:  STN graph objects
# Output: PNG files with plots
#########################################################################
rm(list = ls(all = TRUE))

library(igraph)
library(ggplot2)
library(ggraph)
library(RColorBrewer)
library(reshape2)
# library(ggpubr)  # commented out locally: unused in this file, dependency chain incompatible with R 4.1.2

isets<- c("MOEAD/","NSGA2/") # sets of instances to process

infolder <- "stns/mowflop_x80/"
outfolder <- "plots/mowflop_x80/"

MyShapes <-  c(15)          # Shape for start nodes

MyPal <- c("#4daf4a")      # Color for start nodes

# Shape  and color for  Pareto front
pShape <-   23              
pColor <- "#377eb8"
pSize <- 2.5  # 2.5 for N = 16, 0.8 for N = 128
pAlpha <-0.9 # 1.0 for N = 16, 0.6 for N = 128

# -----------------------------------------------------------------------------
# Plot the complete STN without vector's differentiation
# Two alternative layouts: force directed (graphopt) and using the Objective space
# instance: Data file to process
# alg: Name of the algorithms
# bObjLay: Boolean True for Objective layout, False for Force-Dorectd layout
# -----------------------------------------------------------------------------

plot_stn <- function(instance, iset, bObjLay) {
   fname <- paste0(infolder,iset,instance)
   load(fname, verbose = F)
   t <- strsplit(instance, "_")[[1]]
  # tit <- paste0(t[1]," r=",t[3], " m=",t[4], " n=",t[5], " k=",t[6])
   # MoWFLOP fix: the original title (algorithm + instance only) can't tell
   # apart two configs of the same instance in the same panel -- add the
   # config (t[6], e.g. "p100i50") so every subplot has a unique label.
   tit <- paste0(t[1], " ", t[3], " ", t[6])
   print(tit)
   if (length(which(V(STN)$Position =="End")) > 0 ) {   # If there are End Positions
      MyShapes <- c(MyShapes, 17)
      MyPal <-  c(MyPal,"#ff7f00")
   }
   
   if (length(which(V(STN)$Position == "Medium")) > 0 ) {   # If there are Medium Positions
      MyShapes <- c(MyShapes, 1)
      MyPal <-  c(MyPal,"gray50")
   }
   
   if (length(which(V(STN)$Position == "Pareto")) > 0 ) {   # If there are Pareto Positions
      MyShapes <- c(MyShapes, 16)
      MyPal <-  c(MyPal,"#ca0020" )
   }
   
   if (bObjLay == T) {
      mylay <- create_layout(STN, layout = 'grid')
      mylay$x <- V(STN)$f1
      mylay$y <- V(STN)$f2
      # MoWFLOP fix: `mSTN` was never defined anywhere in this script (bug
      # in the original) -- the actual graph object built above is `STN`.
      p <- ggraph(STN, layout = mylay) +
         
         geom_edge_diagonal2(aes(alpha = Count)) + 
         scale_shape_manual(name = "Node Type", values=c(MyShapes, pShape))+ 
         geom_point(data = pf, aes(x=f1, y=f2, color="x_Pareto", shape = "x_Pareto"), 
                    size = pSize, alpha = pAlpha )+
         geom_node_point(aes(shape = Position, size = Count, color=Position)) +
         scale_colour_manual(name = "Node Type", values= c(MyPal, pColor)) +
         scale_size(range = c(0.7, 4.2)) +
         labs(title=tit, x="f1", y="f2") +
         theme_grey() +
         theme(text = element_text(size = 15))
   } else {
      p <- ggraph(STN, layout = 'graphopt') + 
         geom_edge_link(aes(alpha = Count)) + 
         scale_shape_manual(values=MyShapes)+
         geom_node_point(aes(shape = Position, size = Count, color = Position)) +
         scale_colour_manual(values=MyPal) +
         scale_size(range = c(0.5, 4)) +
         ggtitle(tit) +
         theme(text = element_text(size = 15))
      }
   return(p)
}


# ------------------------------------------------------------------------
# Two algorithms only 

arrange_plot_fd <- function(o, fname) {
   arr <- ggarrange(a1_fd[[o[1]]], a1_fd[[o[2]]],a1_fd[[o[3]]],
                    a2_fd[[o[1]]], a2_fd[[o[2]]],a2_fd[[o[3]]],
                    common.legend = T, legend="right",
                    nrow=2, ncol=3)
   fname <-paste0(outfolder, fname,"_fd.png")
   ggsave(arr, filename = fname,  device = png, width = 12, height = 8, dpi =150)
}


arrange_plot_of<- function(o, fname) {
   arr <- ggarrange(a1_of[[o[1]]], a1_of[[o[2]]],a1_of[[o[3]]],
                    a2_of[[o[1]]], a2_of[[o[2]]],a2_of[[o[3]]],
                    common.legend = T, legend="right",
                    nrow=2, ncol=3)
   f <-paste0(outfolder, fname,"_of.png")
   # MoWFLOP fix: `png()` (called) opens a stray graphics device as a side
   # effect (it's what left Rplots.pdf behind); `png` (the function itself,
   # as arrange_plot_fd already does) is what ggsave actually wants here.
   ggsave(arr, filename = f,  device = png, width = 12, height = 8, dpi = 150)
}

# ---- Get all files in given input folders -----------------------------
# keep one list for each algorithm

# MoWFLOP fix: list.files() sorts alphabetically, which groups each
# instance's 3 configs together but NOT in increasing P order (e.g.
# "p100i50" sorts before "p10i50" as strings). Re-sort each instance's
# configs by their numeric P value, keeping instance grouping intact,
# so downstream panels are always p10 -> p50 -> p100.
order_by_P <- function(files) {
   inst <- sapply(strsplit(files, "_"), `[`, 3)
   P <- as.numeric(sub(".*_p([0-9]+)i.*", "\\1", files))
   inst_order <- match(inst, unique(inst))  # preserve first-seen instance order
   files[order(inst_order, P)]
}

da1 <- list.files(paste0(infolder,isets[1]))  # filenames in folder
da2 <- list.files(paste0(infolder,isets[2]))  # filenames in folder
da1 <- order_by_P(da1)
da2 <- order_by_P(da2)
da1 <- head(da1, 6)
da2 <- head(da2, 6)

# Force directed layout (fd) -------------------------------------------------------
# One list of plots for each algorithm a1, a2, a3

a1_fd <- lapply(da1, plot_stn, iset = isets[1], bObjLay = F)
a2_fd <- lapply(da2, plot_stn, iset = isets[2], bObjLay = F)


# Objective function  (of) -------------------------------------------------------
# One list of plots for each algorithm a1, a2, a3

a1_of <- lapply(da1, plot_stn, iset = isets[1], bObjLay = T)
a2_of <- lapply(da2, plot_stn, iset = isets[2], bObjLay = T)

# Arrangement contrasting algorithms
#
# MoWFLOP fix: the original picked two fixed, interleaved index sets
# (o = c(1,3,5) / c(2,4,6)) to contrast the rmnk benchmark's k=1 vs k=4
# configs. Here da1/da2 are grouped by instance and, within each instance,
# ordered by increasing P (order_by_P above), and each instance contributes
# exactly 3 consecutive files (its 3 configs: p10, p50, p100), so the
# meaningful grouping is one panel per instance -- 3 configs (columns, P
# increasing left to right) x 2 algorithms (rows) -- instead of an
# arbitrary interleave.
n <- length(da1)
stopifnot(n == length(da2), n %% 3 == 0)

for (k in seq(1, n, by = 3)) {
   o <- k:(k + 2)
   inst <- strsplit(da1[k], "_")[[1]][3]  # e.g. "ns101"
   arrange_plot_fd(o = o, fname = inst)
   arrange_plot_of(o = o, fname = inst)
}


