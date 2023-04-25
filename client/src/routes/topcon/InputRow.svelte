<script lang="ts">
  export let id: string;
  export let name: string;
  export let subtext: string = "";

  export let type: string = "";
  export let filetype: string = "";
</script>

<div class="py-2 flex justify-between items-center">
  <div>
    <label for={id}>{name}</label>
    {#if subtext}
      <p class="text-sm text-gray-500">{subtext}</p>
    {/if}
  </div>

  {#if type === "number"}
    <input
      class="appearance-none outline outline-gray-300 outline-1 rounded px-2 py-1 w-1/4"
      type="number"
      name={id}
      step="0.5"
      min="0"
      placeholder="Enter Number"
    />
  {/if}

  {#if type === "text"}
    <input
      class="appearance-none outline outline-gray-300 outline-1 rounded px-2 py-1 w-1/4"
      type="text"
      name={id}
      placeholder="Enter Text"
    />
  {/if}

  {#if type === "file"}
    <input type="file" name={id} accept={filetype} />
  {/if}

  <slot />
</div>
