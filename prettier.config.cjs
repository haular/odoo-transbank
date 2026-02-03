/** @type {import('prettier').Config} */

const config = {
    plugins: [require.resolve("@prettier/plugin-xml")],
    bracketSpacing: false,
    printWidth: 126,
    proseWrap: "always",
    tabWidth: 4,
    useTabs: false,
    semi: true,
    trailingComma: "es5",
    xmlWhitespaceSensitivity: "ignore",
};

module.exports = config;
