import {getObjectBrowserStore} from "$lib/browserStore";
import type {Writable} from "svelte/store";

class AppSettings {
    constructor(
        public hidden: string[],
        ) {}
}

export let appSettings: Writable<AppSettings> = getObjectBrowserStore('settings', new AppSettings(
    [],
))
