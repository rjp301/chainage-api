import type { PageLoad } from "./$types";

export const load: PageLoad = async ({fetch }) => {
  const response = await fetch(`http://127.0.0.1:8000/api/topcon`);
  const data = await response.json();
  return {
    topconRuns: data,
  };
};
