<script lang="ts">
    import {Group, Text} from "@svelteuidev/core";

    export let value: any
    export let text: string

</script>


<!--<Group position="right" direction="column" spacing="xs">-->
<div class="flex flex-col gap-1">
    <Text weight="bold" size="md">{value}</Text>
    <Text size="sm" class="text-gray-600 mr-auto">{text}</Text>
</div>
