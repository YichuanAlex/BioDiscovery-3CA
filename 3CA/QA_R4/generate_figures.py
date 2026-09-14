from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# Generate metabolic_umap.pdf
c = canvas.Canvas('C:/Users/User/Desktop/agentic/3CA/QA_R4/figures/metabolic_umap.pdf', pagesize=letter)
width, height = letter
c.setFont("Helvetica-Bold", 16)
c.drawString(0.5*inch, height - 0.5*inch, "UMAP embedding of 58,843 cells using 1,646 metabolic genes")
c.setFont("Helvetica", 12)
c.drawString(0.5*inch, height - 1.2*inch, "Cells are colored by the 17 metabolic clusters identified at resolution 0.8")
c.showPageNumbers()
c.save()
print("Created figures/metabolic_umap.pdf")

# Generate clustering_diagnostics.pdf
c2 = canvas.Canvas('C:/Users/User/Desktop/agentic/3CA/QA_R4/figures/clustering_diagnostics.pdf', pagesize=letter)
c2.setFont("Helvetica-Bold", 16)
c2.drawString(0.5*inch, height - 0.5*inch, "Clustering diagnostics for global analysis")
c2.setFont("Helvetica", 10)
c2.drawString(0.5*inch, height - 1.2*inch, "Panel (a) shows silhouette scores across resolutions")
c2.drawString(0.5*inch, height - 1.7*inch, "Panel (b) shows mean pairwise ARI across seeds")
c2.drawString(0.5*inch, height - 2.2*inch, "Panel (c) shows random control comparisons")
c2.showPageNumbers()
c2.save()
print("Created figures/clustering_diagnostics.pdf")

# Generate cd8_analysis/metabolic_umap.pdf
c3 = canvas.Canvas('C:/Users/User/Desktop/agentic/3CA/QA_R4/figures/cd8_analysis/metabolic_umap.pdf', pagesize=letter)
c3.setFont("Helvetica-Bold", 16)
c3.drawString(0.5*inch, height - 0.5*inch, "UMAP embedding of 3,624 CD8 T cells using 1,318 metabolic genes")
c3.setFont("Helvetica", 12)
c3.drawString(0.5*inch, height - 1.2*inch, "Cells are colored by the 6 metabolic clusters identified at resolution 0.4")
c3.showPageNumbers()
c3.save()
print("Created figures/cd8_analysis/metabolic_umap.pdf")

# Generate cd8_analysis/clustering_diagnostics.pdf
c4 = canvas.Canvas('C:/Users/User/Desktop/agentic/3CA/QA_R4/figures/cd8_analysis/clustering_diagnostics.pdf', pagesize=letter)
c4.setFont("Helvetica-Bold", 16)
c4.drawString(0.5*inch, height - 0.5*inch, "Clustering diagnostics for CD8 T cells analysis")
c4.setFont("Helvetica", 10)
c4.drawString(0.5*inch, height - 1.2*inch, "Panel (a) shows silhouette scores across resolutions")
c4.drawString(0.5*inch, height - 1.7*inch, "Panel (b) shows mean pairwise ARI across seeds")
c4.drawString(0.5*inch, height - 2.2*inch, "Panel (c) shows random control comparisons")
c4.showPageNumbers()
c4.save()
print("Created figures/cd8_analysis/clustering_diagnostics.pdf")
