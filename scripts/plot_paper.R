# Draws any STN (.RData) in the format of the CEC 2027 paper figures, using plot_stn from plot.R unchanged.
# Usage: Rscript scripts/plot_paper.R --layout of|fd [--column] [--position-strip OUT.png] [--lib DIR] --outdir DIR file.RData ...
# Paper figures made with R 4.5.2, ggplot2 4.0.2, ggraph 2.2.2, igraph 2.1.4.

# paper format
PANEL_IN   <- c(width = 1.715, height = 1.25)   # one STN in a 2-per-row subfigure
COLUMN_IN  <- c(width = 1.13,  height = 0.95)   # three STNs in one column
STRIP_WIDTH_IN <- 3.4                           # shared Position legend
DPI        <- 600
MARK_SCALE <- 1.715 / 9          # old figures: ggsave 9 in wide, shrunk by LaTeX
FONT_PT    <- 4.5                # legend items, axis numbers
TITLE_PT   <- 5                  # legend titles, f1 / f2
KEY_PT     <- c(width = 5.5, height = 4)   # legend key
TITLE_GAP_PT <- 0                # legend title -> first item
TEXT_GAP_PT  <- 1                # key -> its label
BLOCK_GAP_PT <- 0.5              # between Position, Visits and Transitions
BOX_GAP_PT   <- 1                # panel -> legend
STRIP_TITLE_GAP_PT <- 3          # strip: "Position" -> first item
STRIP_ITEM_GAP_PT  <- 4          # strip: between items
PLOT_MARGIN_PT <- c(2, 1, 2, 2)  # t, r, b, l
OF_BREAKS  <- c(1.0, 1.5, 2.0)   # f1 and f2 ticks in the "of" view
OF_LABEL_FMT <- "%.1f"
REF_LABEL  <- "Reference set"
POSITIONS  <- c("Begin", "Medium", "End", "Pareto")

# plot_stn from plot.R
# plot.R ends with a driver for its own 2 x 3 panels, so only the lines up to
# the end of plot_stn are evaluated (the first "return(p)" and the "}" after
# it, as cut_prefix in run_plot_r.py), in an environment of their own.
load_plot_stn <- function(plot_r) {
   src <- readLines(plot_r)
   i <- which(trimws(src) == "return(p)")[1]
   stopifnot(!is.na(i))
   j <- i + which(trimws(src[(i + 1):length(src)]) == "}")[1]
   stopifnot(!is.na(j))
   env <- new.env()
   eval(parse(text = src[1:j]), envir = env)
   env
}

# helpers
finite_range <- function(x) { x <- x[is.finite(x)]; if (length(x)) range(x) else NULL }
inst_of <- function(f) strsplit(f, "_")[[1]][3]
has_geom <- function(layer, cls) inherits(layer$geom, cls)
int_lab <- function(x) format(x, scientific = FALSE, trim = TRUE, big.mark = "")

# "of" window of one instance: nodes and reference front of every STN of that
# instance in the same folder (both algorithms, every config), as run_plot_r
of_window <- function(stn, infolder, inst) {
   win <- NULL
   for (iset in stn$isets) {
      for (f in list.files(paste0(infolder, iset))) {
         if (inst_of(f) != inst) next
         e <- new.env()
         load(paste0(infolder, iset, f), envir = e)
         xr <- finite_range(c(e$nodes$f1, e$pf$f1))
         yr <- finite_range(c(e$nodes$f2, e$pf$f2))
         win <- if (is.null(win)) list(x = xr, y = yr) else
            list(x = range(c(win$x, xr)), y = range(c(win$y, yr)))
      }
   }
   win
}

# node size range, edge width, point outline and the reference front's fixed
# size x MARK_SCALE; returns the new node size range
scale_marks <- function(p) {
   # ggplot2 4.0 keeps the palette as a ggproto method; the range plot_stn
   # passed is still in the call that built the scale
   old_range <- eval(p$scales$get_scales("size")$call$range)
   stopifnot(is.numeric(old_range), length(old_range) == 2)
   # default point outline: the theme's geom borderwidth (read without
   # building the plot, which for "of" costs as much as drawing it)
   borderwidth <- calc_element("geom", ggplot2:::plot_theme(p))$borderwidth
   for (L in p$layers) {   # layers are ggproto (environments): edited in place
      if (has_geom(L, "GeomEdgePath")) {
         base <- L$aes_params$edge_width
         if (is.null(base)) base <- L$geom$default_aes$edge_width
         L$aes_params$edge_width <- base * MARK_SCALE
      } else if (has_geom(L, "GeomPoint")) {
         stroke <- L$aes_params$stroke
         if (is.null(stroke)) stroke <- borderwidth
         L$aes_params$stroke <- stroke * MARK_SCALE
         if (!is.null(L$aes_params$size)) L$aes_params$size <- L$aes_params$size * MARK_SCALE
      }
   }
   old_range * MARK_SCALE
}

# min rounded up, middle, max rounded down (2 significant digits): the breaks
# stay inside the trained range, so none is dropped
three_breaks <- function(r) {
   step_of <- function(x) max(1, 10^(floor(log10(abs(x))) - 1))
   mid <- mean(r)
   unique(c(ceiling(r[1] / step_of(r[1])) * step_of(r[1]),
            round(mid / step_of(mid)) * step_of(mid),
            floor(r[2] / step_of(r[2])) * step_of(r[2])))
}

# fixed legend: Position (every type) / Visits / Transitions
fixed_legend <- function(p, graph, of, size_range) {
   pos <- POSITIONS
   # reference front ("of" only): plot_stn maps it to one constant level in
   # colour and shape; that level is renamed REF_LABEL in the layer and in the
   # named manual values, so colour and shape stay matched
   ref_old <- NULL
   if (of) {
      for (L in p$layers) {
         if (!has_geom(L, "GeomPoint") || "size" %in% names(L$mapping)) next
         ref_old <- rlang::eval_tidy(L$mapping$colour)
         stopifnot(is.character(ref_old), identical(ref_old, rlang::eval_tidy(L$mapping$shape)))
         m <- L$mapping
         m$colour <- rlang::quo(!!REF_LABEL)
         m$shape <- rlang::quo(!!REF_LABEL)
         L$mapping <- m
      }
      stopifnot(!is.null(ref_old))
      pos <- c(pos, REF_LABEL)
   }
   stopifnot(all(unique(as.character(igraph::V(graph)$Position)) %in% pos))
   # what each scale is trained on: every node (size), the non-loop edges
   # (ggraph does not draw loops) (alpha)
   node_b <- three_breaks(range(igraph::V(graph)$Count))
   edge_b <- three_breaks(range(igraph::E(graph)$Count[!igraph::which_loop(graph)]))
   # colours and shapes are plot_stn's (MyPal / MyShapes), read from its scales
   shape_vals <- p$scales$get_scales("shape")$palette(length(pos))
   col_vals <- p$scales$get_scales("colour")$palette(length(pos))
   if (!is.null(ref_old)) {
      names(shape_vals)[names(shape_vals) == ref_old] <- REF_LABEL
      names(col_vals)[names(col_vals) == ref_old] <- REF_LABEL
   }
   stopifnot(all(pos %in% names(shape_vals)), all(pos %in% names(col_vals)))
   alpha_range <- eval(formals(ggraph::scale_edge_alpha_continuous)$range)
   # ggplot2 >= 3.5 draws a key only for levels the layer has in its data: the
   # node layer draws every Position key, the reference-front layer none
   for (L in p$layers) {
      if (!has_geom(L, "GeomPoint")) next
      L$show.legend <- if ("size" %in% names(L$mapping))
         c(shape = TRUE, colour = TRUE, size = TRUE) else FALSE
   }
   suppressMessages(p +
      scale_shape_manual(name = "Position", values = shape_vals, limits = pos,
                         breaks = pos, labels = pos, drop = FALSE) +
      scale_colour_manual(name = "Position", values = col_vals, limits = pos,
                          breaks = pos, labels = pos, drop = FALSE) +
      scale_size(name = "Visits", range = size_range, breaks = node_b, labels = int_lab) +
      ggraph::scale_edge_alpha_continuous(name = "Transitions", range = alpha_range,
                                          breaks = edge_b, labels = int_lab) +
      guides(shape = guide_legend(order = 1), colour = guide_legend(order = 1),
             size = guide_legend(order = 2), edge_alpha = guide_legend(order = 3)))
}

# no title, paper fonts, compact legend on the right aligned to the panel top,
# theme lines x MARK_SCALE, "of" ticks
paper_theme <- function(p, of) {
   # in "of" the last x tick label ("2.0") is centred on the panel's right
   # edge: the panel-legend gap gets half of the widest one
   box_gap <- BOX_GAP_PT
   if (of) box_gap <- box_gap + max(vapply(sprintf(OF_LABEL_FMT, OF_BREAKS), function(lab)
      grid::convertWidth(grid::grobWidth(grid::textGrob(lab, gp = grid::gpar(fontsize = FONT_PT))),
                         "pt", valueOnly = TRUE), numeric(1))) / 2
   p <- p + labs(title = NULL, subtitle = NULL) +
      theme(text = element_text(size = FONT_PT),
            legend.position = "right",
            legend.title = element_text(size = TITLE_PT, margin = margin(b = TITLE_GAP_PT)),
            legend.text = element_text(size = FONT_PT, margin = margin(l = TEXT_GAP_PT)),
            legend.key.size = unit(KEY_PT[["width"]], "pt"),
            legend.key.height = unit(KEY_PT[["height"]], "pt"),
            legend.key.spacing = unit(0, "pt"),
            legend.spacing = unit(BLOCK_GAP_PT, "pt"),
            legend.margin = margin(0, 0, 0, 0),
            legend.box.margin = margin(0, 0, 0, 0),
            legend.box.spacing = unit(box_gap, "pt"),
            legend.location = "panel",
            legend.justification.right = "top")
   p <- p + theme(plot.margin = do.call(margin, c(as.list(PLOT_MARGIN_PT), unit = "pt")))
   # grid, ticks and panel outline inherit the root line/rect widths
   th <- ggplot2:::plot_theme(p)
   p <- p + theme(line = element_line(linewidth = calc_element("line", th)$linewidth * MARK_SCALE),
                  rect = element_rect(linewidth = calc_element("rect", th)$linewidth * MARK_SCALE))
   if (of) {
      fmt <- function(x) sprintf(OF_LABEL_FMT, x)
      p <- suppressMessages(p + scale_x_continuous(breaks = OF_BREAKS, labels = fmt) +
                                scale_y_continuous(breaks = OF_BREAKS, labels = fmt))
   }
   # axis.text is rel(0.8) in theme_grey, so it is set explicitly -- only where
   # the plot shows it (ggraph blanks the axes of "fd")
   th <- ggplot2:::plot_theme(p)
   for (el in c("axis.text", "axis.title")) {
      if (!inherits(calc_element(el, th), "element_blank"))
         p <- p + do.call(theme, setNames(list(element_text(size = if (el == "axis.title")
            TITLE_PT else FONT_PT)), el))
   }
   p
}

# the Position guide of p alone, in one row
draw_position_strip <- function(p, out) {
   ps <- p + guides(size = "none", edge_alpha = "none",
                    shape = guide_legend(order = 1, nrow = 1),
                    colour = guide_legend(order = 1, nrow = 1)) +
      theme(legend.position = "bottom", legend.direction = "horizontal",
            legend.title.position = "left",
            legend.title = element_text(size = TITLE_PT, vjust = 0.5,
                                        margin = margin(r = STRIP_TITLE_GAP_PT)),
            legend.key.spacing.x = unit(STRIP_ITEM_GAP_PT, "pt"))
   gs <- ggplot_gtable(ggplot_build(ps))
   strip <- gs$grobs[[which(gs$layout$name == "guide-box-bottom")]]
   w <- grid::convertWidth(grid::grobWidth(strip), "in", valueOnly = TRUE)
   h <- grid::convertHeight(grid::grobHeight(strip), "in", valueOnly = TRUE)
   dev.off()
   if (w > STRIP_WIDTH_IN) stop(sprintf("Position legend %.3f in wider than %.3f in", w, STRIP_WIDTH_IN))
   png(out, width = STRIP_WIDTH_IN, height = h + 2 / 72.27, units = "in", res = DPI, bg = "white")
   grid::grid.newpage()
   grid::grid.draw(strip)
   dev.off()
}

# one STN
draw_paper <- function(stn, rdata, layout, column = FALSE, strip_out = "", outdir = ".") {
   of <- layout == "of"
   infolder <- paste0(dirname(dirname(rdata)), "/")   # .../stns/mowflop_<tag>/
   iset <- paste0(basename(dirname(rdata)), "/")      # MOEAD/ or NSGA2/
   f <- basename(rdata)
   stn$infolder <- infolder                            # read by plot_stn
   p <- stn$plot_stn(f, iset, bObjLay = of)
   if (of) {
      win <- of_window(stn, infolder, inst_of(f))
      if (!is.null(win)) p <- p + coord_cartesian(xlim = win$x, ylim = win$y)
   }
   size_range <- scale_marks(p)
   p <- suppressMessages(p + scale_size(range = size_range))

   # the PNG device is opened before any text is measured, so the measures use
   # its own font metrics
   fig <- if (column) COLUMN_IN else PANEL_IN
   out <- file.path(outdir, paste0(sub("\\.RData$", "", f), "_", layout,
                                   if (column) "_paper_col.png" else "_paper.png"))
   # --position-strip: the panel's device is only used to measure the legend
   measure <- tempfile(fileext = ".png")
   on.exit(unlink(measure), add = TRUE)
   png(if (nzchar(strip_out)) measure else out,
       width = fig[["width"]], height = fig[["height"]], units = "in", res = DPI, bg = "white")

   e <- new.env()
   load(rdata, envir = e)
   p <- fixed_legend(p, e$STN, of, size_range)
   if (column && !nzchar(strip_out)) p <- p + guides(shape = "none", colour = "none")
   p <- paper_theme(p, of)

   if (nzchar(strip_out)) {
      draw_position_strip(p, strip_out)
      cat("->", strip_out, "\n")
      return(invisible(strip_out))
   }
   g <- ggplot_gtable(ggplot_build(p))
   grid::grid.newpage()
   grid::grid.draw(g)
   dev.off()
   cat("->", out, "\n")
   invisible(out)
}

# command line
main <- function(args = commandArgs(trailingOnly = TRUE)) {
   opt <- list(layout = "", column = FALSE, strip = "", outdir = "", lib = "")
   files <- character()
   i <- 1
   while (i <= length(args)) {
      a <- args[i]
      if (a == "--column") { opt$column <- TRUE; i <- i + 1; next }
      key <- switch(a, "--layout" = "layout", "--position-strip" = "strip",
                    "--outdir" = "outdir", "--lib" = "lib", NA)
      if (!is.na(key)) { opt[[key]] <- args[i + 1]; i <- i + 2; next }
      if (startsWith(a, "--")) stop("unknown option: ", a)
      files <- c(files, a); i <- i + 1
   }
   if (!opt$layout %in% c("of", "fd") || !nzchar(opt$outdir) || !length(files))
      stop("usage: plot_paper.R --layout of|fd [--column] [--position-strip OUT.png] ",
           "[--lib DIR] --outdir DIR file.RData ...")
   if (nzchar(opt$strip) && length(files) != 1) stop("--position-strip takes one .RData")
   missing <- files[!file.exists(files)]
   if (length(missing)) stop("not found: ", paste(missing, collapse = ", "))
   if (nzchar(opt$lib)) .libPaths(c(opt$lib, .libPaths()))
   dir.create(opt$outdir, showWarnings = FALSE, recursive = TRUE)

   # plot.R lives next to this file
   me <- sub("^--file=", "", grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE))
   stn <- load_plot_stn(file.path(dirname(normalizePath(me)), "plot.R"))
   for (rdata in normalizePath(files))
      draw_paper(stn, rdata, opt$layout, opt$column, opt$strip, normalizePath(opt$outdir))
}

if (sys.nframe() == 0L) main()
