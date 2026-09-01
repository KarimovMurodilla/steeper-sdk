import { Component, type ErrorInfo, type ReactNode } from "react";
import { ErrorState } from "@/components/ui/ErrorState";

interface Props {
  children: ReactNode;
  /** Changing this value resets the boundary — pass the current route key. */
  resetKey?: string;
}

interface State {
  error: Error | null;
}

/**
 * Catches render-time crashes so one broken page does not blank the whole app.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidUpdate(prev: Props) {
    if (prev.resetKey !== this.props.resetKey && this.state.error) {
      this.setState({ error: null });
    }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Unhandled UI error", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <ErrorState
          title="This page crashed"
          description={this.state.error.message}
          onRetry={() => this.setState({ error: null })}
          className="h-full"
        />
      );
    }
    return this.props.children;
  }
}
