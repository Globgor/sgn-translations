# Working Ukrainian glossary for SGN and breeding interfaces

Draft for Alex's review. This is a consistency aid, not an official or approved terminology standard. Terms follow the current Ukrainian SGN catalog where that usage is clear; alternatives and unresolved choices are called out below. Keep actual organism, accession, trait, project, and person names, IDs, units, stored values, machine keys, and file headers exactly as supplied by the data or interface contract.

| English term | Chosen Ukrainian rendering | Alternatives / disputed choices |
|---|---|---|
| Accession | зразок | Current PO uses both «зразок» and «акцесія». Prefer «зразок» for breeder-facing UI; settle one catalog-wide form after Alex reviews it. |
| Accession name | назва зразка | Keep accession names themselves unchanged. |
| Accession synonym | синонім зразка | A synonym is an alternate name, not a translated name. |
| Stock | матеріал | Broader than accession: a record can represent an accession, plant, plot, cross, or other biological material. PO uses «Назва матеріалу» for Stock Name. Avoid «запас». |
| Stock name | назва матеріалу | Prefer over «назва запасу»; preserve the actual stock name. |
| Seedlot | партія насіння | Existing PO usage; keep distinct from a seed sample or seed count. |
| Seedlot name | назва партії насіння | The seedlot identifier/name remains data. |
| Seedlot transaction | операція з партією насіння | UI wording only; never translate the machine key seedlot_transaction. |
| Seed quantity | кількість насіння | Preserve the numeric value and its unit. |
| Seed weight | маса насіння | Preserve the number and original unit; do not convert it. |
| Trial | дослід | Existing PO usage. Avoid switching casually to «випробування» within one workflow. |
| Trial name | назва досліду | Keep the entered name unchanged. |
| Trial type | тип досліду | Existing PO usage. |
| Trial design | схема досліду | Preferred for the planned layout and allocation; «дизайн досліду» is also seen but sounds less natural. |
| Field design | схема поля | Preserve the design algorithm name and parameters. |
| Field layout | схема розміщення на полі | Short UI alternative: «схема поля». |
| Plot | ділянка | Existing PO usage; distinguish a plot from a field/site. |
| Plot identifier | ідентифікатор ділянки | Keep the identifier and machine field name unchanged. |
| Entry | матеріал у досліді | Context-dependent: may mean a tested line/material, a trial entry, or a row in a file. Avoid translating it as «запис» without context. |
| Block | блок | In a trial design, a block is a design unit; preserve its label/number. |
| Replicate | повторення | Preferred for an experimental replicate. «Повтор» is shorter; «репліка» can sound like a copy. |
| Fieldbook | Fieldbook | Product name; keep the spelling and any application identifier unchanged. |
| Breeding program | селекційна програма | Existing PO usage. |
| Location | місце | Existing PO usage, but qualify in context: «місце проведення» for a trial and «місце зберігання» for inventory. |
| Location name | назва місця | Preserve the actual location name. |
| Cross | схрещування | Existing PO usage for the breeding cross; preserve cross names and parent links. |
| Crossing experiment | дослід зі схрещування | Distinguish the experiment/project from an individual cross. |
| Cross name | назва схрещування | The cross name is data, even when it resembles a pedigree. |
| Pedigree | родовід | Existing UI usage; lineage names and parent relationships are data. |
| Parent | батьківська форма | Prefer for a breeding parent; «батько/мати» is less suitable when sex is unknown or irrelevant. |
| Progeny | потомство | Existing PO usage. |
| Progeny count | кількість нащадків | Preserve the count and any configured maximum. |
| Self | самозапилення | For self-pollination/selfing; do not change a stored cross-type key. |
| Backcross | зворотне схрещування | Preserve the cross type/code in files and APIs. |
| Family | сім’я | In breeding, a related group; «родина» is possible but less consistent with the current catalog. |
| Population | популяція | Preserve population names and identifiers. |
| Generation | покоління | Preserve generation codes and numbers. |
| Germplasm | генетичний матеріал | «Генофонд» can mean the broader resource collection, rather than one material. |
| Plant | рослина | Preserve plant identifiers and names. |
| Trait | ознака | Standard breeder-facing choice; preserve ontology terms and trait identifiers. |
| Trait value | значення ознаки | Preserve the value, category, and scale exactly. |
| Phenotype | фенотип | Use for the biological phenotype; «фенотипові дані» when referring to recorded observations. |
| Phenotypic data | фенотипові дані | Preserve observations, dates, units, and values. |
| Genotype | генотип | Preserve genotype strings, alleles, and identifiers. |
| Genotypic data | генотипові дані | Preserve matrices, marker names, and machine formats. |
| Observation | спостереження | A recorded measurement or categorical value; do not imply a translated scientific result. |
| Observation unit | одиниця спостереження | Preserve the underlying unit and its code. |
| Variable | змінна | In BrAPI/ontology contexts, distinguish a displayed label from the canonical variable key. |
| Ontology | онтологія | Preserve ontology term names/IDs unless the source explicitly provides a reviewed translated label. |
| Scale | шкала | Preserve category labels and numeric bounds as defined by the data source. |
| Unit of measure | одиниця виміру | Never convert or localize the stored unit code. |
| Dataset | набір даних | Keep dataset names and identifiers unchanged. |
| List | список | For a BreedBase List object; use «перелік» in ordinary prose where it reads more naturally. |
| Upload | завантажити до системи | Current PO sometimes uses just «Завантажити»; direction is clearer in help text. Keep upload headers and payload fields canonical. |
| Download | завантажити з системи | Current PO distinguishes this in navigation; avoid ambiguity with Upload. |
| Import | імпортувати | Keep file headers, API names, and parser keys unchanged. |
| Export | експортувати | Keep output column names and machine formats unchanged. |
| Create | створити | Use for a new record or object; do not alter the associated endpoint. |
| Edit | редагувати | Existing PO usage. |
| Save | зберегти | Existing PO usage. |
| Cancel | скасувати | Existing PO usage. |
| Close | закрити | Existing PO usage. |
| Reset | скинути | Existing PO usage. Use «очистити» only when the action specifically clears fields or values. |
| Delete | видалити | Existing PO usage; the confirmation must state exactly what data is affected. |
| Public | загальнодоступний | Existing PO usage; inflect to agree with the noun. «Публічний» is a possible shorter variant. |
| Published | опубліковано | Existing PO usage for a publication status; use «опублікований» only as an adjective. |
| Curator | куратор | Existing domain term; role and permissions remain unchanged. |
| Submitter | користувач, який подав дані | Existing PO wording. «Подавець» is shorter but less established in the current catalog. |
| Researcher | дослідник | Keep person names and affiliations as supplied. |
| Institution | установа | Preserve the institution's registered name and acronym. |

| Genotyping plate | планшет для генотипування | Keep the plate name, ID and 96/384 layout values unchanged. |
| Well | лунка | Plate position and well identifiers remain canonical. |
| Tissue sample | зразок тканини | Preserve tissue-sample names and barcode payloads. |
| Genotyping facility | установа генотипування | Preserve registered facility/vendor names. |
| Genotyping protocol | протокол генотипування | Protocol names and identifiers stay as supplied. |
| Plate layout | схема планшета | File columns and well coordinates remain canonical. |
| Marker | маркер | Translate captions only; preserve marker IDs and names. |
| Allele | алель | Preserve allele symbols and encoded values. |
| Allele dosage | доза алеля | Preserve numeric dosage values and units. |
| Reference genome | референсний геном | Preserve reference genome names, versions and coordinates. |
| Alternate allele | альтернативний алель | Keep ALT/REF fields and encoded allele values unchanged. |
| Genotype calling | визначення генотипів | A genotype call is a determined genotype, not a software call. |
| Genomic site | геномна позиція | Use position for genomic context, not website terminology. |
| Ploidy | плоїдність | Do not alter ploidy values or genotype encoding. |
| Genetic deletion | делеція | Distinct from Delete, which removes an application record. |
| Genetic insertion | інсерція | Preserve variant representation and padding-base rules. |
| Imputation | імпутація | Explain the label only; do not perform or change imputation. |

## Invariants

- Translate labels and explanatory text, not biological names, user-entered names, IDs, values, units, machine keys, or canonical import/export headers.
- Keep Fieldbook and other product/service names unchanged.
- Treat “accession” versus “stock” as a key distinction: an accession is one kind of stock/material, while stock is the broader BreedBase record concept.
- Review the competing PO forms for “Accession” («зразок» / «акцесія») and the short forms for Upload/Download before standardizing the catalog.

## Wave2 genotypes and markers — first-package additions

| English term | Ukrainian rendering | Scope note |
|---|---|---|
| Genetic fingerprint | генетичний профіль | Human QC guidance only; no fingerprint calculation is authorized. |
| Quality control (QC) | контроль якості | Keep QC, KASP and vendor names where they identify a format or assay. |
| Reference allele | референсний алель | UI label; preserve REF/ref and actual allele values. |
| Genetic map | генетична карта | Keep map identifiers, coordinates and original map units. |
| Facility identifier | ідентифікатор від установи генотипування | A per-sample identifier assigned by the genotyping facility, not the institution record ID; preserve facility_identifier and its value. |

## Wave2 analysis — first-package additions

| English term | Ukrainian rendering | Scope note |
|---|---|---|
| Analysis | аналіз | Stored analysis records and authored UI; never run calculations for localization. |
| Mixed model | змішана модель | Preserve lme4/sommer/spl2D engine names and formula syntax. |
| Heritability | успадковуваність | Preserve h2 and all calculated values. |
| GRM | матриця геномної спорідненості (GRM) | Keep GRM in method/file identifiers; no matrix computation. |
| GWAS | повногеномний асоціативний аналіз (GWAS) | Preserve GWAS and method parameters. |
| BLUP | найкращий лінійний незміщений прогноз (BLUP) | Use BLUP/BLUPs where the UI names a method or output; preserve file headers. |
| BLUE | найкраща лінійна незміщена оцінка (BLUE) | Keep BLUE/BLUEs method/output codes. |
| GEBV | геномна оцінка селекційної цінності (GEBV) | Preserve GEBV and accession-specific values. |
| Selection index | селекційний індекс | Human label only; do not alter weights, formulas or rankings. |
| Adjusted mean | скориговане середнє | No calculation or correction of missing-as-zero behavior. |
| Fixed factor | фіксований фактор | Preserve variable/factor names supplied by data. |
| Random factor | випадковий фактор | Preserve model formulas and supplied factor names. |
| Outlier | викид | Existing analysis UI; no filtering is performed during verification. |

## QTL interface additions — Batch37

| English term | Chosen Ukrainian rendering | Boundary |
|---|---|---|
| QTL mapping | картування QTL | Preserve QTL, marker/trait/population names and genomic positions. |
| Genetic map | генетична карта | Preserve map names, versions, positions and cM. |
| Permutation test | перестановочний тест | Caption only; permutation count and calculations remain unchanged. |
| Confidence interval | довірчий інтервал | Preserve numeric limits and confidence percentage. |
| Bayesian credible interval | байєсівський інтервал правдоподібності | Distinct from a confidence interval; preserve the stated method and 95%. |
| Recurrent parent | рекурентна батьківська форма | Preserve the actual parent's accession/name. |
| Donor parent | батьківська форма-донор | Preserve the actual parent's accession/name. |

QTL statistical select options have no explicit value attributes, so their text is also the submitted scientific value. Single-QTL Scan, Marker Regression, Maximum Likelihood, Haley-Knott Regression, Multiple Imputation, Calculate, Simulate, zero and None stay literal. Translate separate captions/tooltips only.

## solGS interface additions — Batch38

| English term | Ukrainian rendering | Boundary |
|---|---|---|
| Genomic prediction | геномне прогнозування | Preserve actual predictions, scientific values and model names. |
| Training population | навчальна популяція | Human caption only; generated stored names/descriptions remain canonical. |
| Selection population | популяція для відбору | Preserve population IDs, names and membership. |
| Genotyping protocol | протокол генотипування | Preserve protocol names/IDs; missing raw values remain explicit. |
| Cached output | кешовані результати | Caption only; localization verification never generates scientific cache files. |
| GEBVs | геномні оцінки селекційної цінності (GEBVs) | Keep the plural scientific token in existing output labels and all file formats. |

## solGS result-label additions — Batch39

| English term | Ukrainian rendering | Boundary |
|---|---|---|
| Model accuracy | точність моделі | Display-copy label only; canonical Mean accuracy lookup and validation-file content unchanged. |
| Cross-validation | перехресна перевірка | Preserve K, fold/run counts and calculated values. |
| Error variance | дисперсія похибки | Scientific numeric variance remains canonical. |
| Inbreeding coefficient | коефіцієнт інбридингу | Caption only; matrix coefficients untouched. |
| Kinship coefficient | коефіцієнт спорідненості | Caption only; matrix/data labels untouched. |

## Shared solGS tools — Batch40

| English term | Ukrainian rendering | Boundary |
|---|---|---|
| PCA | аналіз головних компонент (PCA) | Preserve PCA/PC1/PC2/PCs and numeric scores/loadings. |
| Clustering | кластеризація | Method enums, K and raw group assignments unchanged. |
| Genetic gain | генетичний прогрес | Caption only; no gain/distribution calculation. |
| Ownership (public/private selector) | доступ | Actual cell values encode access, not a person's name; raw API values unchanged. |
| Dendrogram | дендрограма | Caption only; Newick tree format/content unchanged. |
| Tool compatibility | сумісність інструментів | Unknown/not-calculated states remain explicit; no compatibility calculation. |

## NIRS and drone image interfaces (Wave2, first package 42)

| English | Ukrainian UI | Boundary |
|---|---|---|
| NIRS | NIRS | Preserve the acronym, wavelengths and source spectra. |
| Spectra / spectral model | спектри / спектральна модель | Caption only; no fitted model or values are changed. |
| Spectrometer | спектрометр | Keep device names and format identifiers exact. |
| Training / test dataset | навчальний / тестовий набір даних | Keep dataset names and IDs exact. |
| Imaging event | сеанс знімання | Keep event names, timestamps and type values exact. |
| Spectral band | спектральний канал | Keep canonical band tokens exact. |
| Orthophoto | ортофотознімок | Keep filenames, coordinates and pixel data exact. |
| Stock / stock ID | матеріал / ID матеріалу | Existing glossary term; never «запас». |
| EXIF / barcode | EXIF / штрихкод | Keep embedded metadata and barcode payloads exact. |

## Aerial image geometry and analytics (Wave2 package 43)

| English | Ukrainian UI | Boundary |
|---|---|---|
| Ground control point (GCP) | наземна опорна точка (GCP) | Keep point names, coordinates, CRS and stored geometry exact. |
| Plot polygon / polygon | контур ділянки / контур | Display wording only; GeoJSON Polygon type and API keys remain literal. |
| Orthophotomosaic | ортофотомозаїка | Preserve images and pixel values. |
| Imaging pass | прохід знімання | Keep camera positions, order and GPS values exact. |
| Standard process | стандартна обробка | A caption is not scientific runtime acceptance. |
| Vegetative index | вегетаційний індекс | Keep TGI/VARI/NDVI/NDRE names, formulas, bands and coefficients exact. |
| Growing degree days (GDD) | сума ефективних температур (GDD) | Preserve temperatures, units, base values and the existing calculation. |
| Zonal statistics | зональні статистики | Keep generated statistic keys and values literal. |
| Aerial image type options | canonical English descriptions | Keep the two Aerial Medium/Low Res type values and descriptions exact. |

## Climate interface (Wave2 package44)

| English | Ukrainian UI | Boundary |
|---|---|---|
| Environment stratification | стратифікація середовищ | Keep environment IDs/names, GxE tests, alpha and group IDs exact. |
| Latitude / longitude | широта / довгота | Keep all coordinate values/CRS exact. |
| Precipitation | опади | Preserve measurement units and values. |
| Cumulative values by year | накопичені значення за роками | A label does not qualify weather calculations. |
| Location | місце | Existing glossary; keep actual place/station names unchanged. |

## Administration captions (Wave2 package45)

| English | Ukrainian UI | Boundary |
|---|---|---|
| Data agreement | угода щодо даних | UI/editor caption only; actual policy/agreement text and Toronto agreement name unchanged. |
| Recent activity | остання активність | Preserve returned event/count/date data. |
| Required privileges | потрібні права | Keep role enums and access checks exact. |
| Catalog item | позиція каталогу | Preserve actual item names, IDs and ordering behavior. |

## Jobs and Reports UI (Wave2 package46)

| English | Ukrainian UI | Boundary |
|---|---|---|
| Job | завдання | Keep IDs,names,type enums,commands andworker state exact. |
| Dismiss job | видалити запис журналу завдання | Removes the submission record;not resulting analyses/data. Do notsoften to hide. Older qualified forms remain unchanged pending owner-wide review. |
| Cancel job | скасувати завдання | UIcaption only;backend action isnotexecuted. |
| Submitted / finished / failed / timed_out | надіслано / завершено / помилка / час вичерпано | Display renderer only;canonical lowercase status strings andsorting/filter/export values remain raw. |
| Report | звіт | No scientific report/file/email generation orcontent translation. |

## People and forum interface additions — Batch47

| English term | Ukrainian rendering | Boundary |
|---|---|---|
| User account | обліковий запис користувача | Preserve usernames, stored role enums and auth behavior. |
| Directory | довідник | Contact directory; names, organizations and addresses remain data. |
| Forum topic | тема форуму | Preserve stored topic names and identifiers. |
| Forum post | допис | Preserve the authored post body and links. |
| User comment | коментар користувача | API HTML remains raw; localize only known display metadata. |

## Human integration interface additions — Batch48

| English term | Ukrainian rendering | Boundary |
|---|---|---|
| Login | вхід / увійти | Heading versus button; no change to authentication. |
| Authorization | авторизація / надання доступу | Consent only; preserve client names, URLs and grant/deny decisions. |
| OIDC provider | сервіс входу | Preserve the provider identifier and raw error/code/description data. |
| Access token | токен доступу | Human explanation only; never translate or expose token values. |

## Owned widget caption additions — Batch49

| English term | Ukrainian rendering | Boundary |
|---|---|---|
| Collect Date | дата збору даних | Fixed metadata caption only; preserve %Y-%m-%d and date values. |
| Value | значення | Tooltip prefix; raw values never enter the translator. |
| Frequency | частота | Fixed tooltip caption; preserve actual values and all unit/axis data. |
| Histogram | гістограма | Error explanation only; never calculate binning for localization. |
| AND / OR / WHERE / NOT | І / АБО / ДЕ / НЕ | CSS pseudo-captions only; machine operators and query semantics stay canonical. |

## Current calendar and image interfaces (package51)

| English | Ukrainian UI | Boundary |
|---|---|---|
| Calendar / event | календар / подія | Keep stored event type names, dates, time masks and IDs raw. |
| Display order | порядок показу | Keep the numeric order and request fields exact. |
| Thumbnail / original | мініатюра / оригінал | Keep size keys and file URLs exact. |
| Associated tags | пов’язані мітки | Keep user-supplied tags and names raw. |
| Compare images | порівняти зображення | Caption only; no pixel calculation or image modification. |
