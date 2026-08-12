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
library(ggpubr)

isets<- c("MOEAD/","NSGA2/") # sets of instances to process

infolder <- "stns/n16_m2/"
outfolder <- "plots/n16_m2/"

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
   tit <- paste0(t[1]," r = ",t[3])
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
   ggsave(arr, filename = f,  device = png(), width = 12, height = 8, dpi = 150)
}

# ---- Get all files in given input folders -----------------------------
# keep one list for each algorithm
da1 <- list.files(paste0(infolder,isets[1]))  # filenames in folder
da2 <- list.files(paste0(infolder,isets[2]))  # filenames in folder

# Force directed layout (fd) -------------------------------------------------------
# One list of plots for each algorithm a1, a2, a3

a1_fd <- lapply(da1, plot_stn, iset = isets[1], bObjLay = F)
a2_fd <- lapply(da2, plot_stn, iset = isets[2], bObjLay = F)


# Objective function  (of) -------------------------------------------------------
# One list of plots for each algorithm a1, a2, a3

a1_of <- lapply(da1, plot_stn, iset = isets[1], bObjLay = T)
a2_of <- lapply(da2, plot_stn, iset = isets[2], bObjLay = T)

# Arrangement contrasting algorithms 
# Force directed layout
#K = 1: c(1, 3, 5) rmnk
arrange_plot_fd(o = c(1, 3, 5), fname = "k1") 
#K = 4: c(2, 4, 6)
arrange_plot_fd(o = c(2, 4, 6), fname = "k4") 


# Force directed layout
#K = 1: c(1, 3, 5) rmnk
arrange_plot_of(o = c(1, 3, 5), fname = "k1") 
#K = 4: c(2, 4, 6)
arrange_plot_of(o = c(2, 4, 6), fname = "k4") 


