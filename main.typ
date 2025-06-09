#import "@preview/uwnibook-color:0.1.0": *

#let sans = ("Noto Sans", "Noto Sans CJK SC", "Noto Sans SC")
#let serif = ("New Computer Modern", "Noto Serif CJK SC", "Noto Serif SC")
#set text(font: serif, lang: "zh", region: "CN")

#let book-data = json("toc.json")

#let imgs = (
  none, none, none, none, none, none, none, none, none, none,
  none, none, none, none, none, none, none, none, none, none,
  none, none, none, none, none, none, none, none, none, none,
  none, none, none, none, none, none, none, none, none, none,
  none, none, none, none, none, none, none, none, none, none,
  none, none, none, none, none, none, none, none, none, none,
  none, none, none, none, none, none, none, none, none, none,
  none, none, none, none, none, none, none, none, none, none,
  none, none, none, none, none, none, none, none, none, none,
  none, none, none, none, none, none, none, none, none, none,
  none, none, none, none, none, none, none, none, none, none,
  none, none, none, none, none, none, none, none, none, none,
  none, none, none, none, none, none, none, none, none, none,
  none, none, none, none, none, none, none, none, none, none,
  none, none, none, none, none, none, none, none, none, none,
  none, none, none, none, none, none, none, none, none, none,
  none, none, none, none, none, none, none, none, none, none,
  none, none, none, none, none, none, none, none, none, none,
  none, none, none, none, none, none, none, none, none, none,
  none, none, none, none, none, none, none, none, none, none,
  none, none, none, none, none, none, none, none, none, none,
  none, none, none, none, none, none, none, none, none, none,
  none, none, none, none, none, none, none, none, none, none,
  none, none, none, none, none, none, none, none, none, none,
  none, none, none, none, none, none, none, none, none, none,
  none, none, none, none, none, none, none, none, none, none,
);

#let (
  template,
  titlepage,
  outline,
  mainbody,
  appendix,
  proposition,
  highlighteq,
  example,
  definition,
  proof,
  components,
  make-index,
  note,
  notefigure,
  wideblock,
  subheading,
) = config-uwni(
  /// ["en"|"zh"|"lzh"]
  preset: "zh",
  title: (
    zh: [
      #text(font: serif, book-data.title)
    ],
  ),
  // author information
  author: (en: "RainPPR", zh: book-data.authors.join(", ")),
  // author affiliation
  affiliation: text(font: serif, book-data.subtitle),
  // report date
  date: datetime.today(),
  // set to true to enable draft watermark, so that you can prevent from submitting a draft version
  draft: false,
  // set to true to enable two-sided layout
  two-sided: true,
  // "modern"|"classic"
  title-style: "book",
  chap-imgs: imgs,
)

/// make the title page
#titlepage

#show: template

#preamble[
  = 序言

  #for paragraph in book-data.info.abstract [
    #text(font: serif, paragraph)
  
  ]

  #align(center + bottom)[
    #text(font: serif, book-data.info.publishing)
  ]
]

/// make the abstract
#outline()

// this is necessary before starting your main text
#mainbody[
  #for chapter in book-data.content [
    #heading(level: 1, outlined: true)[
      #text(font: serif, chapter.title, size: 1.5em)
    ]
    #for section in chapter.sections [
      #set page(margin: 0pt, header: none, footer: none)
      #place(dx: -1000pt, dy: -1000pt, heading(level: 2, outlined: true)[
        #text(font: serif, section.title)
      ])
      #for page in section.pages [
        #image(page, width: 100%, height: 100%, fit: "cover")
      ]
    ]
  ]
]

// #appendix[
// = 附錄標題
// #lorem(50)
// == 小節標題2
// #lorem(50)
// ]

/// make the bibliography
// #bibliography("citation.bib")

/// make the index
#make-index()
