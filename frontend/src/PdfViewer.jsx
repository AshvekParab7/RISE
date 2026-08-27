import { useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight, FileText } from "lucide-react";
import { GlobalWorkerOptions, getDocument, Util } from "pdfjs-dist";
import workerUrl from "pdfjs-dist/build/pdf.worker.min.mjs?url";

GlobalWorkerOptions.workerSrc = workerUrl;

export default function PdfViewer({ file, citation }) {
  const panelRef = useRef(null);
  const canvasRef = useRef(null);
  const [document, setDocument] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [panelWidth, setPanelWidth] = useState(600);
  const [pageRatio, setPageRatio] = useState(1);
  const [highlights, setHighlights] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const observer = new ResizeObserver((entries) =>
      setPanelWidth(entries[0].contentRect.width),
    );
    if (panelRef.current) observer.observe(panelRef.current);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    let active = true;
    let loadedDocument;
    setError("");
    setDocument(null);
    setPageNumber(1);
    file
      .arrayBuffer()
      .then((data) => getDocument({ data }).promise)
      .then((pdf) => {
        loadedDocument = pdf;
        if (active) setDocument(pdf);
      })
      .catch(() => active && setError("This PDF could not be displayed."));
    return () => {
      active = false;
      loadedDocument?.destroy();
    };
  }, [file]);

  useEffect(() => {
    if (citation?.page) setPageNumber(citation.page);
  }, [citation]);

  useEffect(() => {
    if (!document || !canvasRef.current) return undefined;
    let cancelled = false;
    let renderTask;
    document
      .getPage(pageNumber)
      .then(async (page) => {
        const base = page.getViewport({ scale: 1 });
        const availableWidth = Math.max(panelWidth - 36, 120);
        const scale = Math.min(
          1.5,
          Math.max(0.25, availableWidth / base.width),
        );
        const viewport = page.getViewport({ scale });
        setPageRatio(base.width / base.height);
        const canvas = canvasRef.current;
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        canvas.style.width = `${viewport.width}px`;
        canvas.style.height = `${viewport.height}px`;
        renderTask = page.render({
          canvasContext: canvas.getContext("2d"),
          viewport,
        });
        await renderTask.promise;
        const textContent = await page.getTextContent();
        if (cancelled) return;
        const segments = [];
        let combined = "";
        textContent.items.forEach((item) => {
          const value = item.str || "";
          const start = combined.length;
          combined += `${value} `;
          segments.push({ item, start, end: start + value.length });
        });
        const quote =
          citation?.page === pageNumber
            ? citation.quote?.replace(/\s+/g, " ").trim()
            : "";
        const start = quote
          ? combined
              .replace(/\s+/g, " ")
              .toLowerCase()
              .indexOf(quote.toLowerCase())
          : -1;
        if (start < 0) {
          setHighlights([]);
          return;
        }
        const end = start + quote.length;
        setHighlights(
          segments
            .filter((segment) => segment.end >= start && segment.start <= end)
            .map(({ item }) => {
              const transform = Util.transform(
                viewport.transform,
                item.transform,
              );
              const height = Math.max(Math.abs(transform[3]), 10);
              return {
                left: transform[4],
                top: transform[5] - height,
                width: Math.max(item.width * viewport.scale, 4),
                height,
              };
            }),
        );
      })
      .catch((reason) => {
        if (reason?.name !== "RenderingCancelledException")
          setError("This PDF page could not be displayed.");
      });
    return () => {
      cancelled = true;
      renderTask?.cancel();
    };
  }, [citation, document, pageNumber, panelWidth]);

  return (
    <section className="pdf-panel" ref={panelRef}>
      <header className="pdf-toolbar">
        <div>
          <FileText size={16} />
          <span>{file.name}</span>
        </div>
        <div className="pdf-pages">
          <button
            disabled={pageNumber <= 1}
            onClick={() => setPageNumber((value) => value - 1)}
            aria-label="Previous page"
          >
            <ChevronLeft size={16} />
          </button>
          <span>
            {pageNumber} / {document?.numPages || "..."}
          </span>
          <button
            disabled={!document || pageNumber >= document.numPages}
            onClick={() => setPageNumber((value) => value + 1)}
            aria-label="Next page"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </header>
      {citation?.quote && citation.page === pageNumber && (
        <div className="cited-passage">
          <b>Referenced passage</b>
          <mark>{citation.quote}</mark>
        </div>
      )}
      <div className="pdf-scroll">
        {error ? (
          <p className="api-error">{error}</p>
        ) : (
          <div
            className={`pdf-page ${pageRatio >= 1.15 ? "landscape" : "portrait"}`}
          >
            <canvas ref={canvasRef} />
            {highlights.map((highlight, index) => (
              <span className="pdf-highlight" style={highlight} key={index} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
