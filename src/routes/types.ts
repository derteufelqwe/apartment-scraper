export interface SmallEntry {
    provider: string
    id: string
    title: string
    url: string
    price: number
    size: number
    rooms: number
    address: string | null
    image: string | null
}

export interface ExtendedEntry extends SmallEntry{
    squareMeterPrice: number
}

export interface ServerResponse {
    data: ExtendedEntry[]
}