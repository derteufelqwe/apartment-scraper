<script lang="ts">
    import type {ExtendedEntry, SmallEntry} from "../routes/types";

    import {Badge, Button, Card, Divider, Group, Image, Menu, Text, Title} from "@svelteuidev/core";
    import ValueBox from "$lib/ValueBox.svelte";
    import {CircleBackslash, Gear} from "radix-icons-svelte";
    import {appSettings} from "$lib/settings";

    export let entry: ExtendedEntry;
    $: entrySource = getEntrySource(entry)

    function getEntrySource(entry: ExtendedEntry) {
        switch (entry.provider) {
            case "HausUndGrund":
                return ["Haus und Grund", "providers/HausUndGrund.png"]
            case "SvenOldoerp":
                return ["Sven Oldöerp", "providers/SvenOldoerp.jpg"]
            case "Immowelt":
                return ["Immowelt", "providers/Immowelt.png"]
            case "Immonet":
                return ["Immonet", "providers/Immonet.png"]
            case "MeineStadt":
                return ["MeineStadt", "providers/MeineStadt.png"]
        }

        return ["Unknown", null]
    }

</script>


<Card shadow='xl' padding='md'>
    <div class="grid grid-cols-4">
        <Image
                src='{entry.image ?? undefined}'
                height={160}
                alt='Entry image'
        />
        <div class="col-span-3 ml-3">
            <Group position='apart'>
                <div>
                    <Title weight="semibold" size="lg">{entry.title}</Title>
                    <div class="mb-2"></div>
                </div>
                <div>
                    <slot name="menu"/>
                </div>

            </Group>

            <Group spacing="xs">
                <Image src="location.png" height={12} alt=''/>
                <Text size='sm'>{entry.address}</Text>
            </Group>

            <Divider class="my-3"/>

            <Group spacing="lg" class="ml-4">
                <ValueBox value="{entry.price} €" text="Miete"/>
                <ValueBox value="{entry.size} m²" text="Fläche"/>
                <ValueBox value="{entry.rooms}" text="Zimmer"/>
                <ValueBox value="{entry.squareMeterPrice} €" text="€/m²"/>
            </Group>

            <br>

            <Group spacing="lg" class="ml-4">
                {#if entrySource[1] != null}
                    <Image src="{entrySource[1]}" height={30} alt="{entrySource[0]}"/>
                {/if}
                <Button color='teal' href="{entry.url}" ripple external class="ml-auto">Exposé anzeigen</Button>
            </Group>

        </div>
    </div>

</Card>