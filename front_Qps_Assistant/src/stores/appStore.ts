import { create } from 'zustand'

export type Product = { id: string; name: string; category: string; brand: string; price: number; diagnosis_status: string; creative_status: string; ad_strategy_status: string; review_status: string }
export type Workspace = { product: Product; diagnosis?: any; creative?: any; tasks: any[]; assets: any[]; ad_strategy?: any; metrics: any[]; review?: any; next_actions: string[] }
type State = { products: Product[]; workspace?: Workspace; selectedProduct?: string; setProducts: (products: Product[]) => void; setWorkspace: (workspace: Workspace) => void }
export const useAppStore = create<State>((set) => ({ products: [], setProducts: (products) => set({ products }), setWorkspace: (workspace) => set({ workspace, selectedProduct: workspace.product.id }) }))
