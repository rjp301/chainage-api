import { PrismaClient } from "@prisma/client";
import fs from "fs/promises";
import path from "path";

const prisma = new PrismaClient();

const dataPath = "/Users/riley/Desktop/topcon_runs";

const runs = await fs.readdir(dataPath);
console.log("runs", runs);
for (const run of runs) {
  const fname = path.join(dataPath, run);
  const object = JSON.parse(await fs.readFile(fname));
  object.centerlineId = "64235b612defe8fafb1b2f85";
  object.userId = "64233406f347ea40651dde5b"

  await prisma.topconRun.create({ data: object });
}

console.log("DONE")