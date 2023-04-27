<script lang="ts">
  type option = {
    id: number;
    name: string;
  };

  export let id: string;
  export let label: string;
  export let subtext: string = "";
  export let selectOptions: option[] | undefined = undefined;
</script>

<div class="py-2 flex justify-between items-center">
  <div>
    <label for={id}>{label}</label>
    {#if subtext}
      <p class="text-sm text-gray-500">{subtext}</p>
    {/if}
  </div>

  {#if selectOptions}
    <select
      {id}
      name={id}
      class="appearance-none outline outline-gray-300 outline-1 rounded px-2 py-1 w-1/4"
      {...$$restProps}
    >
      {#each selectOptions as opt}
        <option value={opt.id}>{opt.name}</option>
      {/each}
    </select>
  {:else}
    <input
      {id}
      name={id}
      class="appearance-none outline outline-gray-300 outline-1 rounded px-2 py-1 w-1/4"
      {...$$restProps}
    />
  {/if}

  <slot />
</div>
