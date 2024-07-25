<script lang="ts">
    import {Group, ActionIcon, Text, Anchor, Burger, Tooltip, Image, Title, Button} from '@svelteuidev/core';
    import { Divider, Menu} from '@svelteuidev/core';
    import {ChatBubble, CircleBackslash, Cross1, Gear, MagnifyingGlass, Trash, Width} from "radix-icons-svelte";
</script>

<Group override={{ height: '100%', px: 30 }} position="apart">
    <Anchor
            underline={false}
            href="/"
            override={{ '&:hover': { textDecoration: 'none !important' } }}
            class="my-2"
    >
        <Group>
            <Image
                    src='building.png'
                    height={30}
                    alt='Entry image'
            />
            <Title color="blue" size="xl" weight="semibold">
                Appartment Exposé Scraper
            </Title>
        </Group>
    </Anchor>

    <Menu>
        <Button slot="control">
            <Gear slot="leftIcon"/>
            Einstellungen
        </Button>
        <Menu.Label>Einstellungen</Menu.Label>
        <Menu.Item icon={CircleBackslash} root="a" href="/hidden">Ausgeblendete Anzeigen</Menu.Item>
    </Menu>
</Group>