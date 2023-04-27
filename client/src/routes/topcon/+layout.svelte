<script lang="ts">
  import type { PageData } from "./$types";
  export let data: PageData;
</script>

<aside>
  {#each data.topconRuns as run}
    <a href={`/topcon/${run.id}`}>
      <div>{run.KP_rng}</div>
    </a>
  {/each}
</aside>

<main>
  
</main>

<slot />
