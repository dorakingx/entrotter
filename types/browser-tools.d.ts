// Development-only global injected by the Playwright runner through DevTools.
// The real axe-core declarations describe the loaded library; no runtime stub.
declare const axe: typeof import("axe-core");

// DevTools-only clipboard fault hook registered by Playwright's exposeFunction.
declare function holdCliCopy(text: string): Promise<void>;
