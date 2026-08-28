#!/usr/bin/env Rscript
# entropy (x60noext) vs grid (g1.0noext), for ns178 and 178_r1e-04, all on
# ONE shared node-size (Count) scale and ONE shared node-type legend, so
# every panel here AND in 01_/02_ is directly comparable.
#
#   03_entropy_vs_grid/
#     stn_2x2_of.png   2x2 (rows = scheme, cols = instance), objective-space
#     stn_2x2_fd.png   same, force-directed (graphopt) - pure topology
#     metrics_4way.png facet per S8 metric, 4 bars (instance x scheme), glossary
#     metrics_4way.csv

suppressMessages({ library(igraph); library(ggplot2); library(ggraph); library(patchwork) })

repo <- normalizePath(file.path(dirname(sub("--file=", "",
        grep("--file=", commandArgs(FALSE), value = TRUE))), ".."))
setwd(repo)
outdir <- "/home/elis/Projects/TCC/meeting_2026-08-27/04_sparse_stn_178r1e04/03_entropy_vs_grid"
dir.create(outdir, showWarnings = FALSE, recursive = TRUE)

spec <- list(
  list(inst = "ns178",     scheme = "entropy", tag = "x60noext"),
  list(inst = "178-r1e04", scheme = "entropy", tag = "x60noext"),
  list(inst = "ns178",     scheme = "grid",    tag = "g1.0noext"),
  list(inst = "178-r1e04", scheme = "grid",    tag = "g1.0noext"))
lbl <- function(s) sprintf("%s / %s", ifelse(s$inst == "ns178", "ns178 (base)", "178_r1e-04"), s$scheme)

E <- lapply(spec, function(s) {
  e <- new.env()
  load(sprintf("stns/mowflop_%s/MOEAD/MOEAD_mowflop_%s_2_%s_p10i50_0_post.RData", s$tag, s$inst, s$tag), envir = e)
  e
})
names(E) <- vapply(spec, lbl, "")

# ---- ONE shared scale across all four: nodes (size) AND edges (alpha) ------
cmax <- max(vapply(E, function(e) max(e$nodes$Count), 0))
emax <- max(vapply(E, function(e) max(e$edges$Count), 0))
size_breaks <- unique(round(c(1, cmax/4, cmax/2, cmax)))
edge_breaks <- unique(round(c(1, emax/4, emax/2, emax)))
pos_cols   <- c(Begin = "#4daf4a", End = "#ff7f00", Medium = "gray50", Pareto = "#ca0020")
pos_shapes <- c(Begin = 15,        End = 17,        Medium = 1,         Pareto = 16)
all_pos <- intersect(names(pos_cols),
                     unique(unlist(lapply(E, function(e) as.character(V(e$STN)$Position)))))

# ---- metrics (S8, same formulas as scripts/metrics_stn_mowflop.R) ----------
stn_metrics <- function(e) {
  nodes <- e$nodes; STN <- e$STN; n <- nrow(nodes); nVec <- length(e$weiv)
  pn <- which(V(STN)$Position == "Pareto"); sn <- which(V(STN)$Position == "Begin")
  dg <- distances(STN, v = sn, to = pn, mode = "out", weights = NULL); d <- dg[is.finite(dg)]
  data.frame(nodes = n,
    disc_rate = round(n / sum(nodes$Count), 4), edge_ratio = round(nrow(e$edges) / n, 4),
    shared_vec = round(mean(grepl("_", nodes$Vectors)), 4), pareto = length(pn),
    par_strength = round(sum(strength(STN, vids = pn, mode = "in")) / (e$nRun * nVec), 4),
    n_end = round(sum(nodes$Position == "End") / n, 4), path_par = round(median(d), 4))
}
M <- do.call(rbind, lapply(seq_along(E), function(i)
  cbind(instance = ifelse(spec[[i]]$inst == "ns178", "ns178", "178_r1e-04"),
        scheme = spec[[i]]$scheme, stn_metrics(E[[i]]))))
write.csv(M, file.path(outdir, "metrics_4way.csv"), row.names = FALSE)
print(M)

long <- reshape(M, direction = "long", varying = setdiff(names(M), c("instance", "scheme")),
                v.names = "value", times = setdiff(names(M), c("instance", "scheme")),
                timevar = "metric", idvar = c("instance", "scheme"))
lab <- c(nodes="nodes |N|", disc_rate="disc_rate |N|/B", edge_ratio="edge_ratio |E|/|N|",
         shared_vec="shared_vec", pareto="pareto |Npar|", par_strength="par_strength",
         n_end="n_end frac", path_par="path_par (median)")
long$metric <- factor(lab[long$metric], levels = lab)
long$grp <- paste(long$instance, long$scheme)
glossary <- paste(
 "nodes |N| = distinct STN locations.   disc_rate = nodes / total logged steps (high = little revisiting).",
 "edge_ratio = edges per node.   shared_vec = frac. nodes seen by >1 vector (high = everything funnels through the same choke points).",
 "pareto = nodes reaching the front.   par_strength = incoming weight to Pareto nodes / (runs x vectors).",
 "n_end = frac. nodes that are dead-ends off the front.   path_par = median start->Pareto path; NO BAR = undefined (no Begin nodes).",
 sep = "\n")
gm <- ggplot(long, aes(interaction(scheme, instance), value, fill = grp)) +
  geom_col(width = .7) + geom_text(aes(label = value), vjust = -0.3, size = 2.7) +
  facet_wrap(~ metric, scales = "free_y", nrow = 2) +
  scale_fill_manual(values = c("178_r1e-04 entropy" = "#e41a1c", "178_r1e-04 grid" = "#fb9a99",
                               "ns178 entropy" = "#377eb8", "ns178 grid" = "#a6cee3"), name = NULL) +
  labs(title = "STN metrics (S8): entropy vs grid partitioning, base vs 1e-4 sparse",
       subtitle = "MOEA/D, p10, wind-corrected, external front off", x = NULL, y = NULL,
       caption = glossary) +
  theme_grey(base_size = 11) +
  theme(legend.position = "top", axis.text.x = element_text(angle = 30, hjust = 1, size = 8),
        plot.caption = element_text(hjust = 0, size = 7.5, lineheight = 1.2, margin = margin(t = 10)))
ggsave(file.path(outdir, "metrics_4way.png"), gm, width = 13, height = 8.5, dpi = 150)

# ---- 2x2 STN panels, shared scales ----------------------------------------
panel <- function(e, ttl, mode, show_legend = FALSE) {
  STN <- e$STN; V(STN)$Position <- factor(V(STN)$Position, levels = all_pos)
  if (mode == "of") {
    lay <- create_layout(STN, layout = "grid"); lay$x <- V(STN)$f1; lay$y <- V(STN)$f2
    g <- ggraph(STN, layout = lay) +
      geom_edge_diagonal2(aes(edge_alpha = Count), show.legend = show_legend) +
      geom_point(data = e$pf, aes(x = f1, y = f2), shape = 23, size = 1.8, alpha = .8,
                 colour = "#377eb8", fill = NA) + labs(x = "f1 (cost)", y = "f2 (power)")
  } else {
    set.seed(1)
    g <- ggraph(STN, layout = "igraph", algorithm = "graphopt") +
      geom_edge_link(aes(edge_alpha = Count), show.legend = show_legend) + labs(x = NULL, y = NULL)
  }
  g + geom_node_point(aes(shape = Position, size = Count, colour = Position)) +
    scale_colour_manual(name = "Node type", values = pos_cols[all_pos], drop = FALSE) +
    scale_shape_manual(name = "Node type", values = pos_shapes[all_pos], drop = FALSE) +
    scale_size(name = "node Count", range = c(0.6, 4.2), limits = c(1, cmax), breaks = size_breaks) +
    # shared edge-Count -> opacity, identical in every panel
    scale_edge_alpha(name = "edge Count", range = c(0.05, 0.9),
                     limits = c(1, emax), breaks = edge_breaks) +
    ggtitle(ttl) + theme_grey(base_size = 11)
}
modes <- if (length(commandArgs(TRUE)) && commandArgs(TRUE)[[1]] == "of") "of" else c("of", "fd")
slug <- function(s) sprintf("%s_%s", ifelse(s$inst == "ns178", "ns178", "178r1e04"), s$scheme)
for (mode in modes) {
  # individual panels, each self-contained (keeps its own legend), in panels_<mode>/
  pdir <- file.path(outdir, sprintf("panels_%s", mode))
  dir.create(pdir, showWarnings = FALSE, recursive = TRUE)
  ps <- lapply(seq_along(E), function(i) {
    p <- panel(E[[i]], sprintf("%s  -  %d nodes", names(E)[i], nrow(E[[i]]$nodes)),
               mode, show_legend = TRUE)
    ggsave(file.path(pdir, sprintf("%s.png", slug(spec[[i]]))),
           p, width = 8.5, height = 7, dpi = 150)
    p
  })
  # 2x2: legend once (panel 1), stripped from the rest
  q <- lapply(seq_along(ps), function(i) if (i == 1) ps[[i]] else ps[[i]] + theme(legend.position = "none"))
  combo <- (q[[1]] | q[[2]]) / (q[[3]] | q[[4]]) +
    plot_annotation(
      title = sprintf("entropy (top) vs grid (bottom) - ns178 (left) vs 178_r1e-04 (right) - %s layout", mode),
      subtitle = "all four panels share one node-Count->size scale, one edge-Count->opacity scale, one node-type legend")
  ggsave(file.path(outdir, sprintf("stn_2x2_%s.png", mode)), combo, width = 15, height = 13, dpi = 150)
  cat("wrote stn_2x2_", mode, " + 4 panel_*_", mode, "\n", sep = "")
}
