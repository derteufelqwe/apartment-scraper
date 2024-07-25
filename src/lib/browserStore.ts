import {type Writable, writable} from "svelte/store";


function getBrowserStore(name: string, initial: any, encode: (value: String | null) => any, decode: (value: any | null) => string): Writable<any> {
    let store = writable(encode(window.localStorage.getItem(name) ?? initial));
    store.subscribe((value) => {
        if (value == null) {
            window.localStorage.removeItem(name)
        } else {
            window.localStorage.setItem(name, decode(value))
        }
    })

    return store;
}


export function getNumberBrowserStore(name: string, initial: number | null): Writable<number | undefined> {
    return getBrowserStore(name,
            initial,
            value => Number(value),
            value => String(value),
        );
}

export function getObjectBrowserStore(name: string, initial: any): Writable<any | undefined> {
    return getBrowserStore(name,
            JSON.stringify(initial),
            value => value != null ? JSON.parse(value.toString()) : null,
            value => JSON.stringify(value),
        )
}

// export function getStringBrowserStore(name: string): Writable<String | undefined> {
//     return getBrowserStore(name, value => String(value));
// }
