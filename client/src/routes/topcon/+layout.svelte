<script lang="ts">
  import { page } from "$app/stores";
  import { redirect } from "@sveltejs/kit";
  import type { PageData } from "./$types";
  export let data: PageData;


</script>

<div class="flex w-full">
  <aside class="w-fit h-screen bg-slate-50 sticky top-0 left-0">
    <a href={`/topcon`}>
      <div
        class="py-2 px-4 whitespace-nowrap border-b"
        class:font-bold={$page.url.pathname == "/topcon"}
      >
        ➕ New Calculation
      </div>
    </a>
    {#each data.topconRuns as run}
      <a href={`/topcon/${run.id}`}>
        <div
          class="py-2 px-4 whitespace-nowrap border-b"
          class:font-bold={$page.url.pathname.includes(`/topcon/${run.id}`)}
        >
          {run.KP_rng}
        </div>
      </a>
    {/each}
  </aside>

  <main class="flex-1 px-4 py-2">
    <slot />
  </main>
</div>
