
export async function load({ fetch}) {
    const response = await fetch("/")

    if (response === null) {
        return null;
    }

    return await response.json();
}
