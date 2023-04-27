import type { PageLoad } from "./$types";

export const load: PageLoad = async ({fetch, params }) => {
  const response = await fetch(`http://127.0.0.1:8000/api/topcon/${params.id}`);
  const data = await response.json();
  return {
    topconRun: data,
  };
};
