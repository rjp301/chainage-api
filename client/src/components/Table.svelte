<script lang="ts">
  export let columns: string[];
  export let data: any[];

  const countDecimals = (num: number) => {
    if (Math.floor(num) === num) return 0;
    return num.toString().split(".")[1].length;
  };

  const displayNumber = (num: number, cutoff: number) => {
    if (countDecimals(num) <= cutoff) return num.toString();
    return num.toFixed(cutoff);
  };

  const displayValue = (value: number | string) => {
    if (typeof value === "string") return value;
    return displayNumber(value, 2);
  };
</script>

<div class="relative overflow-x-auto mb-8 p-2">
  <table class="w-full text-center">
    <thead class="uppercase bg-gray-100">
      {#each columns as column}
        <th scope="col" class="px-2 py-1">{column}</th>
      {/each}
    </thead>
    <tbody class="text-sm">
      {#each data as row}
        <tr class="border-t">
          {#each columns as column}
            <td class="px-2 py-1 text-sm">
              {displayValue(row[column])}
            </td>
          {/each}
        </tr>
      {/each}
    </tbody>
  </table>
</div>
