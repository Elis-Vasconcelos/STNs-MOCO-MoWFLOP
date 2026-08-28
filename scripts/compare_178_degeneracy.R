#!/usr/bin/env Rscript
# One-off: directly-comparable STN + metrics, base ns178 vs its 1e-4 sparse
# derivative 178_r1e-04. Both objects are entropy scheme, 60% (Ochoa),
# MOEA/D, p10_i50, wind-corrected, external front OFF (x60noext) -> identical
# pipeline, identical reference-front policy, so the only variable is the
# candidate-grid sparsity.
#
# Fixes the two things that made the meeting-folder pair non-comparable:
#   * shared, fixed Count -> node-size legend (same breaks in both panels)
#   * identical Position colour/shape mapping (Pareto always red)
#
# Outputs into ../meeting_2026-08-27/04_sparse_stn_178r1e04/ :
#   CMP_stn_ns178_vs_178r1e04_of.png   side-by-side STN (objective-space layout)
#   CMP_metrics_ns178_vs_178r1e04.png  grouped bar chart, the S8 metrics
#   CMP_metrics_ns178_vs_178r1e04.csv  the same numbers

suppressMessages({
  library(igraph); library(ggplot2); library(ggraph); library(patchwork)
})

repo <- normalizePath(file.path(dirname(sub("--file=", "",
        grep("--file=", commandArgs(FALSE), value = TRUE))), ".."))
setwd(repo)

# tag drives which partitioning to compare: "x60noext" (entropy 60%, Ochoa)
# or "g1.0noext" (grid, kappa=1). Both instances share the tag.
args <- commandArgs(TRUE)
tag  <- if (length(args) >= 1) args[[1]] else "x60noext"
schemelab <- if (grepl("^g", tag)) {
  sprintf("grid (kappa=%s)", sub("^g([0-9.]+).*", "\\1", tag))
} else {
  sprintf("entropy %s%% (Ochoa)", sub("^x([0-9]+).*", "\\1", tag))
}
sfx <- if (tag == "x60noext") "" else paste0("_", sub("\\.", "", tag))  # file suffix

outdir <- "/home/elis/Projects/TCC/meeting_2026-08-27/04_sparse_stn_178r1e04"
dir.create(outdir, showWarnings = FALSE, recursive = TRUE)

objs <- list(
  ns178      = sprintf("stns/mowflop_%s/MOEAD/MOEAD_mowflop_ns178_2_%s_p10i50_0_post.RData", tag, tag),
  `178_r1e-04` = sprintf("stns/mowflop_%s/MOEAD/MOEAD_mowflop_178-r1e04_2_%s_p10i50_0_post.RData", tag, tag)
)
cat("comparing tag:", tag, "(", schemelab, ")\n")

load_stn <- function(f) { e <- new.env(); load(f, envir = e); e }
E <- lapply(objs, load_stn)

# ---- metrics (references/STN_MoWFLOP.pdf S8, same formulas as
#      scripts/metrics_stn_mowflop.R) -------------------------------------
stn_metrics <- function(e) {
  nodes <- e$nodes; edges <- e$edges; STN <- e$STN
  n  <- nrow(nodes)
  nVec <- length(e$weiv)
  pn <- which(V(STN)$Position == "Pareto")
  sn <- which(V(STN)$Position == "Begin")
  dg <- distances(STN, v = sn, to = pn, mode = "out", weights = NULL)
  d  <- dg[is.finite(dg)]
  data.frame(
    nodes        = n,
    disc_rate    = round(n / sum(nodes$Count), 4),
    edge_ratio   = round(nrow(edges) / n, 4),
    shared_vec   = round(mean(grepl("_", nodes$Vectors)), 4),
    pareto       = length(pn),
    par_strength = round(sum(strength(STN, vids = pn, mode = "in")) / (e$nRun * nVec), 4),
    n_end        = round(sum(nodes$Position == "End") / n, 4),
    path_par     = round(median(d), 4)
  )
}
M <- do.call(rbind, lapply(names(E), function(k) cbind(instance = k, stn_metrics(E[[k]]))))
write.csv(M, file.path(outdir, paste0("CMP_metrics_ns178_vs_178r1e04", sfx, ".csv")), row.names = FALSE)
print(M)

# ---- grouped bar chart, one facet per metric (free y) ------------------
long <- reshape(M, direction = "long", varying = setdiff(names(M), "instance"),
                v.names = "value", times = setdiff(names(M), "instance"),
                timevar = "metric", idvar = "instance")
lab <- c(nodes = "nodes |N|", disc_rate = "disc_rate |N|/B",
         edge_ratio = "edge_ratio |E|/|N|", shared_vec = "shared_vec",
         pareto = "pareto |Npar|", par_strength = "par_strength",
         n_end = "n_end frac", path_par = "path_par (median)")
long$metric <- factor(lab[long$metric], levels = lab)
glossary <- paste(
 "nodes |N|  = number of distinct STN locations.",
 "disc_rate |N|/B  = nodes / total logged steps; high = little revisiting, low = much shared structure.",
 "edge_ratio |E|/|N|  = edges per node (connectivity density).",
 "shared_vec  = fraction of nodes visited by >1 scalarisation vector; high here = all vectors funnel through the same choke points, not 'healthy'.",
 "pareto |Npar|  = number of nodes that reach the reference front.",
 "par_strength  = incoming edge weight to Pareto nodes / (runs x vectors); how much trajectory traffic ends on the front.",
 "n_end frac  = fraction of nodes that are trajectory endpoints and NOT on the front (dead-ends).",
 "path_par  = median shortest directed path length, Begin nodes -> Pareto nodes; UNDEFINED (no bar) when there are no Begin nodes.",
 sep = "\n")
gm <- ggplot(long, aes(instance, value, fill = instance)) +
  geom_col(width = .6) +
  geom_text(aes(label = value), vjust = -0.3, size = 3) +
  facet_wrap(~ metric, scales = "free_y", nrow = 2) +
  scale_fill_manual(values = c(ns178 = "#377eb8", `178_r1e-04` = "#e41a1c")) +
  labs(title = "STN metrics (S8) - base ns178 vs 1e-4 sparse derivative",
       subtitle = sprintf("%s, MOEA/D, p10, wind-corrected, external front off", schemelab),
       x = NULL, y = NULL, caption = glossary) +
  theme_grey(base_size = 12) +
  theme(legend.position = "none", plot.margin = margin(8, 12, 8, 8),
        plot.caption = element_text(hjust = 0, size = 8, lineheight = 1.15,
                                    margin = margin(t = 10)))
ggsave(file.path(outdir, paste0("CMP_metrics_ns178_vs_178r1e04", sfx, ".png")), gm,
       width = 12, height = 8, dpi = 150)

# ---- side-by-side STN, objective-space layout, SHARED fixed scales -----
all_counts <- unlist(lapply(E, function(e) e$nodes$Count))
cmax <- max(all_counts)
size_breaks <- unique(round(c(1, cmax/4, cmax/2, cmax)))
pos_cols   <- c(Begin = "#4daf4a", End = "#ff7f00", Medium = "gray50", Pareto = "#ca0020")
pos_shapes <- c(Begin = 15,        End = 17,        Medium = 1,         Pareto = 16)

# union of node types across BOTH objects, so the shared legend is complete
all_pos <- intersect(names(pos_cols),
                     unique(unlist(lapply(E, function(e) as.character(V(e$STN)$Position)))))
panel <- function(e, ttl, mode) {
  STN <- e$STN
  V(STN)$Position <- factor(V(STN)$Position, levels = all_pos)
  if (mode == "of") {
    lay <- create_layout(STN, layout = "grid")
    lay$x <- V(STN)$f1; lay$y <- V(STN)$f2
    g <- ggraph(STN, layout = lay) +
      geom_edge_diagonal2(aes(alpha = Count), show.legend = FALSE) +
      geom_point(data = e$pf, aes(x = f1, y = f2),
                 shape = 23, size = 2.2, alpha = .9, colour = "#377eb8", fill = NA) +
      labs(x = "f1 (cost)", y = "f2 (power)")
  } else {                       # fd: force-directed (graphopt); objective
    set.seed(1)                  # values do NOT drive position -> no axis mismatch
    g <- ggraph(STN, layout = "igraph", algorithm = "graphopt") +
      geom_edge_link(aes(alpha = Count), show.legend = FALSE) +
      labs(x = NULL, y = NULL)
  }
  g +
    geom_node_point(aes(shape = Position, size = Count, colour = Position)) +
    scale_colour_manual(name = "Node type", values = pos_cols[all_pos], drop = FALSE) +
    scale_shape_manual(name = "Node type", values = pos_shapes[all_pos], drop = FALSE) +
    scale_size(name = "Count", range = c(0.7, 4.2),
               limits = c(1, cmax), breaks = size_breaks) +
    ggtitle(ttl) + theme_grey(base_size = 12)
}
# legend on the LEFT panel only (ns178 -- it has every node type incl. Begin;
# scales are fixed & identical so one legend describes both).
for (mode in c("of", "fd")) {
  p1 <- panel(E[["ns178"]], sprintf("ns178  (base)  -  %d nodes", nrow(E[["ns178"]]$nodes)), mode)
  p2 <- panel(E[["178_r1e-04"]], sprintf("178_r1e-04  (tau/n = 1e-4)  -  %d nodes",
              nrow(E[["178_r1e-04"]]$nodes)), mode) + theme(legend.position = "none")
  sub <- if (mode == "of") "objective-space layout (x=f1, y=f2)"
         else "force-directed layout (graphopt) - position is topology, not objectives"
  combo <- (p1 | p2) + plot_annotation(
    title = sprintf("%s - same partitioning, same legend/scale; only the candidate-grid sparsity differs", schemelab),
    subtitle = sub)
  ggsave(file.path(outdir, sprintf("CMP_stn_ns178_vs_178r1e04_%s%s.png", mode, sfx)), combo,
         width = 16, height = 7, dpi = 150)
}

cat("\nwrote CMP_*", sfx, " (stn _of/_fd, metrics png/csv) into ", outdir, "\n")
