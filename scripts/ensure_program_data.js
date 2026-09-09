/*
 * Creates empty programme files when they are missing.
 *
 * src/data/{sessions,speakers,schedule}.json are fetch artifacts and stay
 * gitignored, but several routes import them directly, so a fresh clone would
 * fail to build without them. `pnpm program:fetch` overwrites these with the
 * real programme once there is one; until then the empty shapes below keep the
 * build honest — no sessions, no speakers, no schedule days.
 */
import fs from "fs";
import path from "path";

const destFolder = "./src/data";

const placeholders = {
	"sessions.json": "{}\n",
	"speakers.json": "{}\n",
	"schedule.json": '{\n  "days": []\n}\n',
};

fs.mkdirSync(destFolder, { recursive: true });

for (const [name, contents] of Object.entries(placeholders)) {
	const dest = path.join(destFolder, name);
	if (fs.existsSync(dest)) continue;
	fs.writeFileSync(dest, contents);
	console.log(`Created empty ${dest}`);
}
