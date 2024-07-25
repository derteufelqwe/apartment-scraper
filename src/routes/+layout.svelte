<script>
    import "../app.css";
    import {SvelteUIProvider} from '@svelteuidev/core';
    import {AppShell, Header} from '@svelteuidev/core';
    import HeadContent from "$lib/HeadContent.svelte";
</script>

<style>
    .bg-color {
        background-color: #f3f3f3;
    }
</style>

<SvelteUIProvider>
    <div class="bg-color">
        <AppShell>
            <Header slot="header" height="20">
                <HeadContent/>
            </Header>

            <slot/>
        </AppShell>
    </div>
</SvelteUIProvider>
