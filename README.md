# atom-samples

Collection of data-flow and usage slice samples
for [appthreat/atom](https://github.com/appthreat/atom).

## Slice Generation

Slices were generated using the following commands, where language is the
programming language of the target project as listed in Sample Sources.

`atom usages -l language -o app.atom -s usages.json .`

`atom reachables -l language -o app.atom -s reachables.json .`

## Sample Sources

Data-flow and usage commands for sample projects below.

| Project                                                       | Type           |
|---------------------------------------------------------------|----------------|
| [apolloconfig/apollo](https://github.com/apolloconfig/apollo) | java           |
| [avajs/ava](https://github.com/avajs/ava)                     | javascript     |
| [axios/axios](https://github.com/axios/axios)                 | javascript     |
| [explosion/spaCy](https://github.com/explosion/spaCy)         | python         |
| [karatelabs/karate](https://github.com/karatelabs/karate)     | java           |
| [msiemens/tinydb](https://github.com/msiemens/tinydb)         | python         |
| [scrapy/scrapy](https://github.com/scrapy/scrapy)             | python         |
| [se2p/pynguin](https://github.com/se2p/pynguin)               | python         |
| [sequelize/sequelize](https://github.com/sequelize/sequelize) | javascript     |
| [sqshq/piggymetrics](https://github.com/sqshq/piggymetrics)   | java           |
| [square/retrofit](https://github.com/square/retrofit)         | java (android) |
| [tornadoweb/tornado](https://github.com/tornadoweb/tornado)   | python         |
| [videojs/video.js](https://github.com/videojs/video.js)       | javascript     |

## Generation Script

generate.py can be used to download the sample sources and generate slices in
linux, or from other sample repositories in a csv modeled
on [sources.csv](sources.csv).