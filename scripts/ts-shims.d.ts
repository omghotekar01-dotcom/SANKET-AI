declare module 'react' {
  export type SetStateAction<S> = S | ((prev:S)=>S)
  export type Dispatch<A> = (value:A)=>void
  export function useState<S>(initial:S|(()=>S)): [S,Dispatch<SetStateAction<S>>]
  export function useRef<T>(initial:T): {current:T}
  export function useEffect(effect:()=>void|(()=>void), deps?:readonly unknown[]): void
  export function useCallback<T extends (...args:any[])=>any>(callback:T,deps:readonly unknown[]):T
  export const StrictMode:any
  export type RefObject<T>={current:T}
  export interface FormEvent { preventDefault():void }
  const React:any; export default React
}
declare module 'react-dom/client' { export const createRoot:any }
declare module 'react/jsx-runtime' { export const jsx:any; export const jsxs:any; export const Fragment:any }
declare interface ImportMeta { env:any }
declare namespace JSX { interface IntrinsicElements { [elemName:string]: any } }
