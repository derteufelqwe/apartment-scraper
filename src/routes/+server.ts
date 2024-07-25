import { error } from '@sveltejs/kit';
import type {ExtendedEntry, SmallEntry} from "./types";

function toExtendedEntry(smallEntry: SmallEntry): ExtendedEntry {
    let res = smallEntry as ExtendedEntry
    res.squareMeterPrice = Math.round(res.price / res.size * 100) / 100.0

    return res
}

/** @type {import('./$types').RequestHandler} */
export async function GET({ url, fetch }) {
    const priceMin = Number(url.searchParams.get('priceMin'));
    const priceMax = Number(url.searchParams.get('priceMax'));
    const rooms = Number(url.searchParams.get('rooms'));
    const area = Number(url.searchParams.get('area'));
    const providers = url.searchParams.get('providers');

    let filters = [];

    if (!isNaN(priceMin) && priceMin > 0) {
        filters.push((e: SmallEntry) => e.price >= priceMin);
    }
    if (!isNaN(priceMax) && priceMax > 0) {
        filters.push((e: SmallEntry) => e.price <= priceMax);
    }
    if (!isNaN(rooms) && rooms > 0) {
        filters.push((e: SmallEntry) => e.rooms >= rooms);
    }
    if (!isNaN(area) && area > 0) {
        filters.push((e: SmallEntry) => e.size >= area);
    }
    if (providers != null) {
        filters.push((e: SmallEntry) => providers.split(',').includes(e.provider));
    }

    const request = await fetch('results.json')
    const response: SmallEntry[] = await request.json()

    let filteredData = response;
    filters.forEach(filter => {
        filteredData = filteredData.filter(filter)
    })

    let extendedData = filteredData.map(toExtendedEntry)

    extendedData.sort((a, b) => a.squareMeterPrice - b.squareMeterPrice)

    return new Response(JSON.stringify({
        data: extendedData,
    }));
}
