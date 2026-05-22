import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = { children: ReactNode };
type State = { error: Error | null };

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[UI] Render error:", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-slate-100 p-6 dark:bg-slate-950">
          <h1 className="text-lg font-semibold text-red-600">Something went wrong</h1>
          <p className="max-w-lg text-center text-sm text-slate-600 dark:text-slate-300">
            {this.state.error.message}
          </p>
          <button
            type="button"
            className="rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white"
            onClick={() => window.location.reload()}
          >
            Reload page
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
