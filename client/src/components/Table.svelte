<script lang="ts">
  export let columns: string[];
  export let data: any[];
</script>

<div class="relative overflow-x-auto mb-8">
  <table class="w-full text-left">
    <thead class="uppercase bg-gray-100">
      {#each columns as column}
        <th scope="col" class="px-2 py-1">{column}</th>
      {/each}
    </thead>
    <tbody class="text-sm">
      {#each data as row}
        <tr class="border-t">
          {#each columns as column}
            <td class="px-2 py-1">{row[column]}</td>
          {/each}
        </tr>
      {/each}
    </tbody>
  </table>
</div>
