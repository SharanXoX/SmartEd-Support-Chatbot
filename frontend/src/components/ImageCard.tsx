import { AnimatePresence, motion } from "framer-motion";
import { useCallback, useEffect, useState } from "react";
import { resolveAssetUrl } from "../api/client";

type Props = {
  src: string;
  alt: string;
  caption?: string;
  stepLabel?: string;
};

export default function ImageCard({ src, alt, caption, stepLabel }: Props) {
  const [open, setOpen] = useState(false);
  const [failed, setFailed] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const url = resolveAssetUrl(src);

  useEffect(() => {
    setFailed(false);
    setLoaded(false);
    if (url) {
      console.info("[IMAGE] Loading:", url);
    }
  }, [url]);

  const close = useCallback(() => setOpen(false), []);

  const handleLoad = () => {
    setLoaded(true);
    setFailed(false);
    console.info("[IMAGE] Loaded OK:", url);
  };

  const handleError = () => {
    setFailed(true);
    setLoaded(false);
    console.error("[IMAGE] Failed to load:", url);
  };

  return (
    <>
      <motion.div layout className="mt-3 overflow-hidden rounded-xl ring-1 ring-slate-200/80 dark:ring-slate-700">
        {stepLabel ? (
          <div className="bg-slate-100 px-3 py-1 text-[11px] font-semibold uppercase tracking-wide text-slate-600 dark:bg-slate-800 dark:text-slate-300">
            {stepLabel}
          </div>
        ) : null}

        {failed ? (
          <div className="flex min-h-[120px] flex-col items-center justify-center gap-2 bg-amber-50 px-4 py-6 text-center dark:bg-amber-950/30">
            <span className="text-xs font-medium text-amber-900 dark:text-amber-100">
              Screenshot unavailable
            </span>
            <span className="break-all text-[10px] text-amber-800/80 dark:text-amber-200/70">{url}</span>
          </div>
        ) : (
          <button
            type="button"
            className="group relative block w-full min-h-[120px] bg-slate-100 text-left dark:bg-slate-900"
            onClick={() => loaded && setOpen(true)}
          >
            {!loaded && !failed ? (
              <div className="absolute inset-0 z-10 flex items-center justify-center text-xs text-slate-500 dark:text-slate-400">
                Loading screenshot…
              </div>
            ) : null}
            <img
              src={url}
              alt={alt}
              loading="lazy"
              decoding="async"
              onLoad={handleLoad}
              onError={handleError}
              className={`max-h-72 w-full cursor-zoom-in object-contain transition duration-300 group-hover:opacity-95 sm:max-h-80 ${
                loaded ? "opacity-100" : "opacity-0"
              }`}
            />
            <span className="sr-only">Expand screenshot</span>
          </button>
        )}

        {caption ? (
          <div className="border-t border-slate-200 px-3 py-2 text-xs text-slate-600 dark:border-slate-800 dark:text-slate-300">
            {caption}
          </div>
        ) : null}
      </motion.div>

      <AnimatePresence>
        {open && loaded && !failed ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
            role="dialog"
            aria-modal="true"
            onClick={close}
          >
            <motion.div
              initial={{ scale: 0.94, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.94, opacity: 0 }}
              transition={{ type: "spring", stiffness: 280, damping: 26 }}
              className="relative max-h-[90vh] max-w-[min(960px,calc(100vw-2rem))] overflow-auto rounded-2xl bg-white p-3 shadow-2xl dark:bg-slate-950"
              onClick={(e) => e.stopPropagation()}
            >
              <button
                type="button"
                className="absolute right-3 top-3 rounded-full bg-slate-900/80 px-3 py-1 text-xs font-semibold text-white hover:bg-slate-900 dark:bg-white/90 dark:text-slate-900"
                onClick={close}
              >
                Close
              </button>
              <img src={url} alt={alt} className="max-h-[82vh] w-full rounded-lg object-contain" />
              {caption ? <div className="mt-2 px-1 text-sm text-slate-700 dark:text-slate-200">{caption}</div> : null}
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </>
  );
}
