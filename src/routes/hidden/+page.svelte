<script lang="ts">

    import {
        Loader, Menu,
        Text,
    } from "@svelteuidev/core";
    import EntryCard from "$lib/EntryCard.svelte";
    import type {ExtendedEntry, ServerResponse, SmallEntry} from "../types";
    import {appSettings} from "$lib/settings";
    import {CircleBackslash, CheckCircled} from "radix-icons-svelte";

    export let data: ServerResponse
    $: filteredData = filterData(data.data, $appSettings.hidden)

    function filterData(data: ExtendedEntry[], hidden: string[]) {
        return data.filter(e => hidden.includes(e.id))
    }

    async function unhideEntry(entry: SmallEntry) {
        $appSettings.hidden = $appSettings.hidden.filter(id => id != entry.id)
        $appSettings = $appSettings
    }

</script>


<div class="grid grid-cols-5 gap-6">
    <div class="col-span-1">
    </div>

    <div class="col-span-3">

        <Text size="lg" weight="semibold" class="mb-3">{filteredData.length} ausgeblendete Ergebnisse
        </Text>
        {#each filteredData as entry}
            <div class="mb-5">
                <EntryCard entry={entry}>
                    <div slot="menu">
                        <Menu>
                            <Menu.Label>Exposé-Optionen</Menu.Label>
                            <Menu.Item icon={CheckCircled} on:click={() => unhideEntry(entry)}>Einblenden</Menu.Item>
                        </Menu>
                    </div>
                </EntryCard>
            </div>
        {/each}

    </div>

    <div class="col-span-1">

    </div>
</div>

