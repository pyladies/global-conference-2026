
//Available social links by default
const defaultLinks = {
    instagram: null,
    linkedin: null,
    mastodon: null,
    bluesky: null,
    twitter: null,
    youtube: null,
    git: null,
    website: null,
};

//Add your info here, follow the existing structure :)
//Possible teams: infrastructure, program, communications, design_media, code_of_conduct
const volunteers = [
    //{
    //    name: "...",
    //    image: "/images/volunteers/...",
    //    links: {
    //        linkedin: "https://www.linkedin.com/...",
    //        git: "https://github.com/...",
    //    },
    //    teams: ["infrastructure"]
    //},
];

//adds the default socials
function applyDefaultLinks(grouped) {
    return Object.fromEntries(
        Object.entries(grouped).map(([team, arr]) => [
            team,
            arr.map(v => ({
                ...v,
                links: { ...defaultLinks, ...v.links }
            }))
        ])
    );
}

function groupByTeams(list) {
    const result = {};

    list.forEach(v => {
        v.teams.forEach(team => {
            team = team.toLowerCase(); // to avoid duplication
            if (!result[team])
                result[team] = [];

            result[team].push(v);
        });
    });

    return result;
}

//shuffle array function
function shuffleArray(array) {
    const arr = [...array];
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
}

function shuffleGroups(grouped) {
    return Object.fromEntries(
        Object.entries(grouped).map(([team, arr]) => [
            team,
            shuffleArray(arr)
        ])
    );
}

// shuffled array


const grouped = groupByTeams(volunteers);
const withDefaults = applyDefaultLinks(grouped);
const volunteersFinal = shuffleGroups(withDefaults);

export default volunteersFinal;
