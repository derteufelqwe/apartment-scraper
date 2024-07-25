<script lang="ts">
    import EntryCard from "$lib/EntryCard.svelte";
    import {
        Button,
        CheckboxGroup,
        Divider,
        Group, Loader, Menu,
        NativeSelect,
        NumberInput,
        Text,
        Title
    } from "@svelteuidev/core";
    import {CircleBackslash, MagnifyingGlass} from 'radix-icons-svelte';
    import type {ExtendedEntry, ServerResponse, SmallEntry} from "./types";
    import {getNumberBrowserStore, getObjectBrowserStore} from "$lib/browserStore";
    import {onMount} from "svelte";
    import {appSettings} from "$lib/settings";

    let data: ServerResponse | null = null;

    const checkboxItems = [
        {label: 'Immowelt', value: 'Immowelt'},
        {label: 'Immonet', value: 'Immonet'},
        {label: 'Haus und Grund', value: 'HausUndGrund'},
        {label: 'Sven Oldöerp', value: 'SvenOldoerp'},
        {label: 'MeineStadt', value: 'MeineStadt'},
    ]

    let priceMin = getNumberBrowserStore("priceMin", null);
    let priceMax = getNumberBrowserStore("priceMax", null)
    let rooms = getNumberBrowserStore("rooms", null)
    let area = getNumberBrowserStore("area", null)
    let providers = getObjectBrowserStore("providers", checkboxItems.map(e => e.value))

    let loading = false;
    $: filteredData = filterData(data?.data ?? null, $appSettings.hidden)
    $: hiddenItemsCnt = filteredData == null || data == null ? null : data.data.length - filteredData.length

    onMount(() => {
        fetchData();
    })

    async function fetchData() {
        loading = true;
        const providersString = $providers?.join(',')
        const request = await fetch(`/?priceMin=${$priceMin}&priceMax=${$priceMax}&rooms=${$rooms}&area=${$area}&providers=${providersString}`);
        data = await request.json();
        loading = false;
    }

    function filterData(data: ExtendedEntry[] | null, hidden: string[]) {
        if (data == null) {
            return null;
        }

        return data.filter(e => !hidden.includes(e.id))
    }

    async function hideEntry(entry: SmallEntry) {
        $appSettings.hidden.push(entry.id)
        $appSettings = $appSettings
    }

</script>


<style>

</style>


<div class="grid grid-cols-5 gap-6">
    <div class="col-span-1 bg-white p-3 rounded shadow-lg">
        <div class="flex flex-col">
            <Title weight="semibold" size="lg">Filtern</Title>
            <Divider class="pb-4"/>

            <Text size="sm" class="pb-2">Kaltmiete</Text>
            <Group noWrap>
                <NumberInput
                        placeholder="Min €"
                        min={100}
                        required={false}
                        hideControls
                        bind:value={$priceMin}
                />
                <Text size="md">–</Text>
                <NumberInput
                        placeholder="Max €"
                        min={100}
                        required={false}
                        hideControls
                        bind:value={$priceMax}
                />
            </Group>

            <div class="pb-4"></div>

            <NativeSelect data={['1', '1.5', '2', '2.5', '3', '3.5', '4', '5']}
                          placeholder="Zimmer"
                          label="Zimmer"
                          required={false}
                          bind:value={$rooms}
            />

            <div class="pb-4"></div>

            <NumberInput
                    placeholder="Größe in m²"
                    label="Wohnfläche"
                    min={0}
                    required={false}
                    hideControls
                    bind:value={$area}
            />

            <div class="pb-4"></div>
            <Text size="sm" class="pb-2">Provider</Text>
            <CheckboxGroup direction="column"
                           items="{checkboxItems}"
                           bind:value={$providers}
            />

            <div class="pb-6"></div>

            <Button class="mx-auto" on:click={(e) => fetchData()} loading="{loading}">
                <MagnifyingGlass slot="leftIcon"/>
                Filtern
            </Button>
        </div>
    </div>

    <div class="col-span-3">
        {#if filteredData != null}
            <Text size="lg" weight="semibold" class="mb-3">{filteredData.length} Ergebnisse ({hiddenItemsCnt} Versteckt)</Text>
            {#each filteredData as entry}
                <div class="mb-5">
                    <EntryCard entry={entry}>
                        <div slot="menu">
                            <Menu>
                                <Menu.Label>Exposé-Optionen</Menu.Label>
                                <Menu.Item icon={CircleBackslash} on:click={() => hideEntry(entry)}>Ausblenden</Menu.Item>
                            </Menu>
                        </div>
                    </EntryCard>
                </div>
            {/each}
        {:else}
            <Loader variant='dots' />
        {/if}
    </div>

    <div class="col-span-1">

    </div>
</div>
