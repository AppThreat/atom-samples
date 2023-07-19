# atom-samples

Collection of data-flow and usage slice samples for [appthreat/atom](https://github.com/appthreat/atom).

## Slice Generation

Slices were generated using the following commands, where language is the programming language of the target project as listed in Sample Sources.
        
`atom data-flow -o app.atom --slice-outfile .\atom-samples\data-flow.json -l language .`

`atom usages -o app.atom --slice-outfile .\atom-samples\usages.json -l language .`

## Sample Sources
Data-flow and usage commands for sample projects below.
|Project|Type|
|-|-|
|[apolloconfig/apollo](https://github.com/apolloconfig/apollo)|java|
|[axios/axios](https://github.com/axios/axios)|typescript|
|[explosion/spaCy](https://github.com/explosion/spaCy)|python|
|[karatelabs/karate](https://github.com/karatelabs/karate)|java|
|[scrapy/scrapy](https://github.com/scrapy/scrapy)|python|
|[se2p/pynguin](https://github.com/se2p/pynguin)|python|
|[sequelize/sequelize](https://github.com/sequelize/sequelize)|javascript|
|[square/retrofit](https://github.com/square/retrofit)|java|
|[videojs/video.js](https://github.com/videojs/video.js)|javascript|


