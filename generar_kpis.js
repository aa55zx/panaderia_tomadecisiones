const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  VerticalAlign, Header, Footer, PageNumber
} = require('docx');
const fs = require('fs');

const border = { style: BorderStyle.SINGLE, size: 4, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };

function headerCell(text, bgColor = "2E5899") {
  return new TableCell({
    borders,
    width: { size: 9360 / 3, type: WidthType.DXA },
    shading: { fill: bgColor, type: ShadingType.CLEAR },
    margins: { top: 100, bottom: 100, left: 150, right: 150 },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text, bold: true, color: "FFFFFF", size: 22, font: "Arial" })]
    })]
  });
}

function dataCell(text, bgColor = "FFFFFF", bold = false, color = "333333") {
  return new TableCell({
    borders,
    width: { size: 9360 / 3, type: WidthType.DXA },
    shading: { fill: bgColor, type: ShadingType.CLEAR },
  
    margins: { top: 80, bottom: 80, left: 150, right: 150 },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({
      children: [new TextRun({ text, bold, size: 20, font: "Arial", color })]
    })]
  });
}

function kpiTable(kpiCode, title, status, statusColor, value, formula, variables, nota) {
  const statusBg = statusColor === "green" ? "D4EDDA" : statusColor === "yellow" ? "FFF3CD" : "F8D7DA";
  const statusTxt = statusColor === "green" ? "1E7E34" : statusColor === "yellow" ? "856404" : "721C24";

  const rows = [
    // Header row: code | title | status
    new TableRow({
      children: [
        new TableCell({
          borders,
          width: { size: 1200, type: WidthType.DXA },
          shading: { fill: "2E5899", type: ShadingType.CLEAR },
          margins: { top: 100, bottom: 100, left: 150, right: 150 },
          verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: kpiCode, bold: true, color: "FFFFFF", size: 24, font: "Arial" })]
          })]
        }),
        new TableCell({
          borders,
          width: { size: 6360, type: WidthType.DXA },
          shading: { fill: "2E5899", type: ShadingType.CLEAR },
          margins: { top: 100, bottom: 100, left: 150, right: 150 },
          verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({
            children: [new TextRun({ text: title, bold: true, color: "FFFFFF", size: 22, font: "Arial" })]
          })]
        }),
        new TableCell({
          borders,
          width: { size: 1800, type: WidthType.DXA },
          shading: { fill: statusBg, type: ShadingType.CLEAR },
          margins: { top: 100, bottom: 100, left: 150, right: 150 },
          verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: status, bold: true, color: statusTxt, size: 20, font: "Arial" })]
          })]
        }),
      ]
    }),
    // Value row
    new TableRow({
      children: [
        new TableCell({
          borders,
          columnSpan: 3,
          width: { size: 9360, type: WidthType.DXA },
          shading: { fill: "F0F4FB", type: ShadingType.CLEAR },
          margins: { top: 120, bottom: 120, left: 150, right: 150 },
          verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: value, bold: true, size: 48, font: "Arial", color: "2E5899" })]
          })]
        }),
      ]
    }),
    // Formula row
    new TableRow({
      children: [
        new TableCell({
          borders,
          columnSpan: 3,
          width: { size: 9360, type: WidthType.DXA },
          shading: { fill: "FFFFFF", type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 150, right: 150 },
          children: [new Paragraph({
            children: [
              new TextRun({ text: "Formula: ", bold: true, size: 18, font: "Arial", color: "555555" }),
              new TextRun({ text: formula, size: 18, font: "Arial", color: "333333" }),
            ]
          })]
        }),
      ]
    }),
    // Variables row
    new TableRow({
      children: [
        new TableCell({
          borders,
          columnSpan: 3,
          width: { size: 9360, type: WidthType.DXA },
          shading: { fill: "F9F9F9", type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 150, right: 150 },
          children: variables.map(v => new Paragraph({
            children: [new TextRun({ text: v, size: 18, font: "Arial", color: "444444" })]
          }))
        }),
      ]
    }),
  ];

  if (nota) {
    rows.push(new TableRow({
      children: [
        new TableCell({
          borders,
          columnSpan: 3,
          width: { size: 9360, type: WidthType.DXA },
          shading: { fill: "E8F4E8", type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 150, right: 150 },
          children: [new Paragraph({
            children: [
              new TextRun({ text: "Nota: ", bold: true, size: 18, font: "Arial", color: "1E7E34" }),
              new TextRun({ text: nota, size: 18, font: "Arial", color: "333333" }),
            ]
          })]
        }),
      ]
    }));
  }

  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [1200, 6360, 1800],
    rows
  });
}

const doc = new Document({
  styles: {
    default: {
      document: { run: { font: "Arial", size: 22 } }
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, font: "Arial", color: "1A3A6B" },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 0 }
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: "2E5899" },
        paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 1 }
      },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 }
      }
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "2E5899", space: 1 } },
          children: [new TextRun({ text: "Dashboard de KPIs — Panaderia El Ranchero", size: 18, font: "Arial", color: "2E5899" })]
        })]
      })
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          border: { top: { style: BorderStyle.SINGLE, size: 6, color: "CCCCCC", space: 1 } },
          children: [
            new TextRun({ text: "Pagina ", size: 18, font: "Arial", color: "888888" }),
            new TextRun({ children: [PageNumber.CURRENT], size: 18, font: "Arial", color: "888888" }),
            new TextRun({ text: " de ", size: 18, font: "Arial", color: "888888" }),
            new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 18, font: "Arial", color: "888888" }),
          ]
        })]
      })
    },
    children: [
      // Titulo principal
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 200 },
        children: [new TextRun({ text: "Dashboard de KPIs", bold: true, size: 52, font: "Arial", color: "1A3A6B" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 80 },
        children: [new TextRun({ text: "Panaderia El Ranchero", bold: true, size: 36, font: "Arial", color: "2E5899" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 400 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: "2E5899", space: 4 } },
        children: [new TextRun({ text: "Indicadores Clave de Rendimiento", size: 22, font: "Arial", color: "666666" })]
      }),

      // KPI 1: TSC
      new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300, after: 100 },
        children: [new TextRun({ text: "1. Tasa de Satisfaccion del Cliente (TSC)", bold: true, font: "Arial", color: "2E5899" })] }),
      kpiTable(
        "TSC",
        "Tasa de Satisfaccion del Cliente",
        "REVISAR",
        "yellow",
        "50.0%",
        "(CP / TP) x 100",
        [
          "CP = Comentarios positivos: 100",
          "TP = Total comentarios: 200",
          "Mide la percepcion positiva de los clientes en base a comentarios.",
        ],
        "Meta: mayor a 70%. Actualmente por debajo del umbral recomendado."
      ),
      new Paragraph({ spacing: { before: 0, after: 200 }, children: [] }),

      // KPI 2: PVC
      new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300, after: 100 },
        children: [new TextRun({ text: "2. Proyeccion de Ventas por Dia (PVC)", bold: true, font: "Arial", color: "2E5899" })] }),
      kpiTable(
        "PVC",
        "Proyeccion de Ventas por Dia",
        "OK",
        "green",
        "$12,491.44",
        "PMC + Ingreso Externo + IE + Dias Especiales",
        [
          "PMC = Ingreso promedio por dia del periodo evaluado",
          "IE = Ingresos extraordinarios",
          "Dias Especiales = ajuste por fechas de alta demanda",
          "Rentable: 168 dias",
        ],
        null
      ),
      new Paragraph({ spacing: { before: 0, after: 200 }, children: [] }),

      // KPI 3: TCL
      new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300, after: 100 },
        children: [new TextRun({ text: "3. Tendencia de Categoria Lider (TCL)", bold: true, font: "Arial", color: "2E5899" })] }),
      kpiTable(
        "TCL",
        "Tendencia de Categoria Lider",
        "OK",
        "green",
        "31.4%",
        "(VC / VT) x 100",
        [
          "VC = Ventas de la categoria lider",
          "VT = Ventas totales del periodo",
          "Identifica la categoria que mas aporta a las ventas totales.",
        ],
        null
      ),
      new Paragraph({ spacing: { before: 0, after: 200 }, children: [] }),

      // KPI 4: RDI
      new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300, after: 100 },
        children: [new TextRun({ text: "4. Ratio de Rotacion de Insumos (RDI)", bold: true, font: "Arial", color: "2E5899" })] }),
      kpiTable(
        "RDI",
        "Ratio de Rotacion de Insumos",
        "Buen Consumo",
        "green",
        "42.16 kg/dia",
        "Total Insumo / DP",
        [
          "Total Insumo = Kilogramos totales de harina consumidos",
          "DP = Dias del periodo evaluado",
          "Mide el promedio de harina consumida por dia de operacion.",
        ],
        "Buen Consumo: mayor a 12 kg/dia. El valor actual supera la meta."
      ),
      new Paragraph({ spacing: { before: 0, after: 200 }, children: [] }),

      // KPI 5: TVFS
      new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300, after: 100 },
        children: [new TextRun({ text: "5. Tasa de Variacion en Fin de Semana (TVFS)", bold: true, font: "Arial", color: "2E5899" })] }),
      kpiTable(
        "TVFS",
        "Tasa de Variacion en Fin de Semana",
        "OK",
        "green",
        "Ver calculo",
        "TVFS = ((VFS - VFS_ant) / VFS_ant) x 100",
        [
          "VFS = Ventas del fin de semana actual",
          "VFS_ant = Ventas del fin de semana anterior",
          "Mide el crecimiento o caida de ventas entre fines de semana.",
        ],
        null
      ),
      new Paragraph({ spacing: { before: 0, after: 200 }, children: [] }),

      // KPI 6: VVC
      new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300, after: 100 },
        children: [new TextRun({ text: "6. Variacion de Ventas por Categoria (VVC)", bold: true, font: "Arial", color: "2E5899" })] }),
      kpiTable(
        "VVC",
        "Variacion de Ventas por Categoria (Fin de Semana)",
        "OK",
        "green",
        "Ver calculo",
        "RAC = (CVFS_dia - PV_dia - EV_dia)",
        [
          "CVFS_dia = Costo de ventas fin de semana por dia",
          "PV_dia = Promedio de ventas diarias",
          "EV_dia = Eventos o ventas extraordinarias por dia",
          "Evalua la rentabilidad por categoria en fines de semana.",
        ],
        null
      ),

      new Paragraph({ spacing: { before: 0, after: 200 }, children: [] }),

      // KPI 7: PMVU
      new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300, after: 100 },
        children: [new TextRun({ text: "7. Producto Mas Vendido por Unidades (PMVU)", bold: true, font: "Arial", color: "2E5899" })] }),
      kpiTable(
        "PMVU",
        "Producto Mas Vendido por Unidades",
        "OK",
        "green",
        "Bolillo  —  177,971 unidades",
        "PMVU = MAX( SUPL(art.Lote) )",
        [
          "Unidades = unidades vendidas por producto por periodo",
          "Identifica el producto estrella con mayor volumen de ventas.",
          "Resultado: Bolillo con 177,971 unidades vendidas.",
        ],
        null
      ),
      new Paragraph({ spacing: { before: 0, after: 200 }, children: [] }),

      // KPI 8: IPT
      new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300, after: 100 },
        children: [new TextRun({ text: "8. Ingreso Promedio por Transaccion (IPT)", bold: true, font: "Arial", color: "2E5899" })] }),
      kpiTable(
        "IPT",
        "Ingreso Promedio por Transaccion",
        "OK",
        "green",
        "$1,203.03",
        "IPT = IT / AT",
        [
          "IT = Ingresos totales del periodo",
          "AT = Numero de transacciones totales",
          "Total de transacciones registradas: 1,969",
          "Mide el ticket promedio por cada venta realizada.",
        ],
        null
      ),
      new Paragraph({ spacing: { before: 0, after: 200 }, children: [] }),

      // KPI 9: TCD
      new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300, after: 100 },
        children: [new TextRun({ text: "9. Tasa de Calidad de Datos (TCD)", bold: true, font: "Arial", color: "2E5899" })] }),
      kpiTable(
        "TCD",
        "Tasa de Calidad de Datos",
        "OK",
        "green",
        "100.0%",
        "(RC / TR) x 100",
        [
          "RC = Registros correctos: 100",
          "TR = Total de registros: 100",
          "Mide consistencia y limpieza de datos almacenados en MongoDB.",
        ],
        null
      ),
      new Paragraph({ spacing: { before: 0, after: 200 }, children: [] }),

      // KPI 10: IEP
      new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300, after: 100 },
        children: [new TextRun({ text: "10. Indice de Estacionalidad del Producto (IEP)", bold: true, font: "Arial", color: "2E5899" })] }),
      kpiTable(
        "IEP",
        "Indice de Estacionalidad del Producto",
        "OK",
        "green",
        "4.86 x",
        "IEP = VS_Mes / IM",
        [
          "VS_Mes = Ventas del mes independiente evaluado",
          "IM = Promedio mensual de ventas del producto",
          "Ratio que expresa cuanto supera (o no) el promedio mensual de ventas.",
          "IEP > 1 = superior al promedio mensual.",
        ],
        null
      ),
      new Paragraph({ spacing: { before: 0, after: 200 }, children: [] }),

      // KPI 11: SNP
      new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300, after: 100 },
        children: [new TextRun({ text: "11. Sentimiento Negativo por Periodo (SNP)", bold: true, font: "Arial", color: "2E5899" })] }),
      kpiTable(
        "SNP",
        "Sentimiento Negativo por Periodo",
        "REVISAR",
        "red",
        "50.0%",
        "(TN / TC) x 100",
        [
          "TN = Total de comentarios negativos: 100",
          "TC = Total de comentarios: 200",
          "Mide cuantas quejas de clientes superan el umbral critico.",
        ],
        "Alerta si supera el 20%. Valor actual muy por encima del limite aceptable."
      ),
      new Paragraph({ spacing: { before: 0, after: 200 }, children: [] }),

      // KPI 12: CIB
      new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 300, after: 100 },
        children: [new TextRun({ text: "12. Costo de Uso de Insumos (CIB)", bold: true, font: "Arial", color: "2E5899" })] }),
      kpiTable(
        "CIB",
        "Costo de Uso de Insumos",
        "OK",
        "green",
        "$97.81 / kg",
        "CIB = IT / TC",
        [
          "IT = Ingresos totales generados: $171,163",
          "TC = Total de insumos usados en kg",
          "Mide el ingreso generado por cada kg de harina utilizado.",
          "Mayor valor = mayor eficiencia en el uso de insumos.",
        ],
        null
      ),

      // Espaciado final
      new Paragraph({ spacing: { before: 400, after: 0 }, children: [] }),

      // Nota final
      new Paragraph({
        alignment: AlignmentType.CENTER,
        border: { top: { style: BorderStyle.SINGLE, size: 4, color: "CCCCCC", space: 2 } },
        spacing: { before: 200, after: 0 },
        children: [new TextRun({ text: "Documento generado el 15 de abril de 2026  |  Panaderia El Ranchero", size: 18, font: "Arial", color: "AAAAAA" })]
      }),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("KPIs_Panaderia_El_Ranchero_v2.docx", buffer);
  console.log("Documento creado: KPIs_Panaderia_El_Ranchero_v2.docx");
});
