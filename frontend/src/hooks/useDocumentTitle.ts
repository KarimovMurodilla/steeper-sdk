import { useEffect } from "react";

const SUFFIX = "Steeper";

/** Sets the tab title for as long as the page is mounted. */
export function useDocumentTitle(title?: string) {
  useEffect(() => {
    const previous = document.title;
    document.title = title ? `${title} · ${SUFFIX}` : SUFFIX;
    return () => {
      document.title = previous;
    };
  }, [title]);
}
