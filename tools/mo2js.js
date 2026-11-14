// msgfmt has already rejected broken input and removed fuzzy and empty entries.
const fs = require('node:fs');
const { mo } = require('gettext-parser');
const parsed = mo.parse(fs.readFileSync(process.argv[2]));
if (!parsed.headers['Plural-Forms']) {
    throw new Error(process.argv[2] + ': no Plural-Forms header');
}
const data = { '': { plural_forms: parsed.headers['Plural-Forms'], language: parsed.headers.Language } };
for (const [context, messages] of Object.entries(parsed.translations)) {
    for (const [id, message] of Object.entries(messages)) {
        if (id) data[context ? context + '\u0004' + id : id] = message.msgstr;
    }
}
process.stdout.write('var sgn_locale_data = ' + JSON.stringify(data) + ';\n');
