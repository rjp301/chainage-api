<script lang="ts">
  import Table from "../../../components/Table.svelte";
  import type { PageData } from "./$types";

  export let data: PageData;
</script>

<div class="flex justify-between items-center">
  <div>
    <h2>Ditch Volume Calculation - {data.topconRun.KP_rng}</h2>
    <p>{new Date(data.topconRun.createdAt)}</p>
  </div>
  <a
    href={`http://127.0.0.1:8000/api/topcon/${data.topconRun.id}/download`}
    class="bg-red-500 px-8 py-2 text-white rounded shadow font-bold"
    download>Download Excel</a
  >
</div>
<br />
<Table
  columns={[
    "num",
    "x",
    "y",
    "z",
    "desc",
    "chainage",
    "slope",
    "width_bot",
    "width_top",
    "area",
  ]}
  data={data.topconRun.data_pts}
/>

<Table
  columns={[
    "KP_beg",
    "KP_end",
    "area_beg",
    "area_end",
    "area_avg",
    "length",
    "volume",
  ]}
  data={data.topconRun.data_rng}
/>
