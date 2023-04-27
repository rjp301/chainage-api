<script>
  import FormInput from "../../components/FormInput.svelte";
</script>

<form method="post" enctype="multipart/form-data" class="grid divide-y px-4">
  <h2>Perform New Ditch Calculation</h2>
  <FormInput
    id="centerlineId"
    label="Centerline"
    selectOptions={[{ value: 1, name: "TMEP S5B 5.24.16" }]}
  />

  <FormInput
    id="slope"
    label="Slope of Ditch Sides [slope:1]"
    type="number"
    placeholder="Select number"
  />

  <FormInput
    id="width_bot"
    label="Width of Ditch Bottom [m]"
    type="number"
    placeholder="Select number"
  />

  <FormInput
    id="ditch_shp"
    type="file"
    accept=".shp"
    label="Designed Ditch Profile [SHP]"
    subtext="3D SHP file of bottom of ditch"
  />

  <FormInput
    id="ground_csv"
    type="file"
    accept=".csv"
    label="Surveyed Ground Profile [CSV]"
    subtext="Survey shots as CSV file in the format ID, X, Y, Z, DESC"
  />

  <FormInput
    id="data_crs"
    label="Data CRS [EPSG:####]"
    type="text"
    subtext="EPSG No. of the Coordinate Reference System used"
    placeholder="Specify CRS"
  />
  <div class="flex gap-4 py-2">
    <button class="px-1 py-1 w-full bg-red-500 rounded text-white" type="submit"
      >Submit</button
    >
    <button class="px-1 py-1 w-full bg-red-500 rounded text-white" type="reset"
      >Reset</button
    >
  </div>
</form>
