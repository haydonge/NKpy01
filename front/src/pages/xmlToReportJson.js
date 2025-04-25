// 将 XML Document 和文件名解析为后端需要的 JSON 结构
// 根据实际 XML 文件结构进行解析

export default function xmlToReportJson(xmlDoc, fileName) {
  // 调试函数 - 打印XML结构
  function debugXmlStructure(doc) {
    console.log('XML文档根元素:', doc.documentElement.tagName);
    
    // 递归遍历XML结构的前几层
    function logElement(element, depth = 0, maxDepth = 2) {
      if (depth > maxDepth) return;
      
      const children = Array.from(element.children);
      if (children.length === 0) return;
      
      const indent = '  '.repeat(depth);
      console.log(`${indent}${element.tagName} 包含子元素: ${children.map(c => c.tagName).join(', ')}`);
      
      if (depth < maxDepth) {
        children.forEach(child => logElement(child, depth + 1, maxDepth));
      }
    }
    
    logElement(doc.documentElement, 0);
  }
  
  // 调试XML结构
  debugXmlStructure(xmlDoc);
  
  // 1. 解析文件名，提取 filename_info
  // 文件名格式: 1M243403498-476352A.101-NET07A00003-1-20250122-201937_Pass.xml
  const baseName = fileName.replace(/\.xml$/i, "");
  const parts = baseName.split("-");
  let filename_info = {};
  if (parts.length >= 6) {
    const lastPart = parts[5].split("_");
    let result = lastPart[1] || '';
    result = result.trim();
    if (["pass", "passed", "passted"].includes(result.toLowerCase())) result = "Pass";
    else if (["fail", "failed"].includes(result.toLowerCase())) result = "Fail";
    filename_info = {
      filename: baseName, // 文件名字段，便于后端写库
      serial_number: parts[0],
      part_number: parts[1],
      tester_id: parts[2],
      test_sub: parts[3],
      date: parts[4],
      time: lastPart[0],
      result: result
    };
  }
  
  // 通用函数 - 安全获取元素文本
  const getElementText = (parent, selector) => {
    try {
      if (!parent) return '';
      const node = parent.querySelector(selector);
      return node ? node.textContent.trim() : '';
    } catch (e) {
      console.error(`获取 ${selector} 失败:`, e);
      return '';
    }
  };
  
  // 通用函数 - 获取元素的属性
  const getElementAttr = (element, attrName) => {
    try {
      return element && element.hasAttribute(attrName) ? element.getAttribute(attrName) : '';
    } catch (e) {
      console.error(`获取属性 ${attrName} 失败:`, e);
      return '';
    }
  };
  
  // 2. 解析 test_info
  // 首先定位关键元素
  const resultData = xmlDoc.querySelector('QM_TEST_RESULT > RESULT_DATA') || xmlDoc.querySelector('RESULT_DATA');
  const headerElement = resultData ? resultData.querySelector('HEADER') : null;
  const timesElement = resultData ? resultData.querySelector('TIMES') : null;
  
  console.log('关键元素:', {
    hasResultData: !!resultData,
    hasHeader: !!headerElement,
    hasTimes: !!timesElement
  });
  
  // 构建 test_info 对象
  const test_info = {
    // 从 HEADER 部分提取信息
    file_name: getElementText(headerElement, 'FILE_NAME'),
    swift_version: getElementText(headerElement, 'SWIFT_VERSION'),
    test_spec_id: getElementText(headerElement, 'TEST_SPEC_ID'),
    operator_id: getElementText(headerElement, 'OPERATOR'),
    
    // 从 TESTER 部分提取信息
    tester_serial_number: getElementText(headerElement, 'TESTER SERIAL_NUMBER'),
    tester_ot_number: getElementText(headerElement, 'TESTER OT_NUMBER'),
    tester_sw_version: getElementText(headerElement, 'TESTER SW_VERSION'),
    tester_hw_version: getElementText(headerElement, 'TESTER HW_VERSION'),
    tester_site: getElementText(headerElement, 'TESTER SITE'),
    tester_operation: getElementText(headerElement, 'TESTER OPERATION'),
    
    // 从 DUT 部分提取信息
    dut_serial_number: getElementText(headerElement, 'DUT SERIAL_NUMBER'),
    dut_product_code: getElementText(headerElement, 'DUT PRODUCT_CODE'),
    dut_product_revision: getElementText(headerElement, 'DUT PRODUCT_REVISION'),
    
    // 提取 CUSTOM_ATTRIBUTES 信息
    custom_attributes: headerElement ? (() => {
      const attrs = headerElement.querySelector('CUSTOM_ATTRIBUTES');
      if (!attrs) return '';
      const fields = Array.from(attrs.querySelectorAll('FIELD'));
      return fields.map(f => `${f.textContent}=${f.getAttribute('VALUE') || ''}`).join(';');
    })() : '',
    
    // 从 TIMES 部分提取信息
    setup_time: getElementText(timesElement, 'SETUP_TIME'),
    test_time: getElementText(timesElement, 'TEST_TIME'),
    unload_time: getElementText(timesElement, 'UNLOAD_TIME'),
    
    // 从 RESULT_DATA 直接子元素提取信息
    test_start: resultData ? getElementText(resultData, 'TEST_START') : '',  // 测试开始时间
    test_stop: resultData ? getElementText(resultData, 'TEST_STOP') : '',    // 测试结束时间
    overall_status: resultData ? getElementText(resultData, 'OVERALL_STATUS') : '', // 总体状态
    
    // 从 DIAGNOSTICS 元素提取信息
    diagnostics_type: (() => {
      const diagnosticsElement = resultData ? resultData.querySelector('DIAGNOSTICS') : null;
      return diagnosticsElement ? getElementAttr(diagnosticsElement, 'TYPE') : '';
    })(),
    diagnostics_value: resultData ? getElementText(resultData, 'DIAGNOSTICS') : '',
  };
  
  // 调试输出关键字段
  console.log('关键 test_info 字段:', {
    test_start: test_info.test_start,
    test_stop: test_info.test_stop,
    overall_status: test_info.overall_status,
    diagnostics_type: test_info.diagnostics_type,
    diagnostics_value: test_info.diagnostics_value
  });
  
  // 3. 解析 measurements
  // 定位 RESULTS 元素
  const resultsElement = resultData ? resultData.querySelector('RESULTS') : null;
  
  // 获取所有 MEASUREMENT 元素
  const measurementElements = resultsElement ? Array.from(resultsElement.querySelectorAll('MEASUREMENT')) : [];
  console.log(`找到 ${measurementElements.length} 个 MEASUREMENT 元素`);
  
  // 如果没有找到测量元素，尝试其他选择器
  if (measurementElements.length === 0 && resultData) {
    const altMeasurements = Array.from(resultData.querySelectorAll('MEASUREMENT'));
    console.log(`使用备用选择器找到 ${altMeasurements.length} 个 MEASUREMENT 元素`);
    if (altMeasurements.length > 0) {
      measurementElements.push(...altMeasurements);
    }
  }
  
  // 如果还是没有找到，尝试直接从根元素搜索
  if (measurementElements.length === 0) {
    const rootMeasurements = Array.from(xmlDoc.querySelectorAll('MEASUREMENT'));
    console.log(`从根元素搜索到 ${rootMeasurements.length} 个 MEASUREMENT 元素`);
    if (rootMeasurements.length > 0) {
      measurementElements.push(...rootMeasurements);
    }
  }
  
  // 如果找到了测量元素，打印第一个元素的结构
  if (measurementElements.length > 0) {
    const firstMeasurement = measurementElements[0];
    console.log('第一个 MEASUREMENT 元素结构:', {
      tagName: firstMeasurement.tagName,
      childNodes: Array.from(firstMeasurement.children).map(c => c.tagName),
      hasID: !!firstMeasurement.querySelector('ID'),
      hasName: !!firstMeasurement.querySelector('n'),
      hasResult: !!firstMeasurement.querySelector('RESULT'),
      hasStatus: !!firstMeasurement.querySelector('STATUS')
    });
  }
  
  // 解析每个测量元素
  const measurements = measurementElements.map(element => {
    // 获取 RESULT 元素
    const resultElement = element.querySelector('RESULT') || element.querySelector('r');
    
    // 获取结果类型和值
    const resultType = resultElement ? getElementAttr(resultElement, 'TYPE') : '';
    const resultValue = resultElement ? resultElement.textContent.trim() : '';
    
    // 获取测量名称 - 首先尝试 NAME 元素，然后尝试 n 元素或 name 属性
    let name = getElementText(element, 'NAME');
    if (!name) {
      name = getElementText(element, 'n') || getElementAttr(element, 'name');
    }
    
    // 调试输出测量名称
    const measurementId = getElementText(element, 'ID');
    console.log(`测量 ID ${measurementId} 的名称: ${name}`);
    
    // 确保名称不为空
    if (!name) {
      console.warn(`警告: 测量 ID ${measurementId} 的名称为空`);
    }
    
    // 获取单位 - 可能在 'UNIT_OF_MEAS' 元素中或作为属性
    let unitOfMeasure = getElementText(element, 'UNIT_OF_MEAS');
    if (!unitOfMeasure) {
      unitOfMeasure = getElementAttr(element, 'unit');
    }
    
    // 获取状态 - 可能在 'STATUS' 元素中或作为属性
    let status = getElementText(element, 'STATUS');
    if (!status) {
      status = getElementAttr(element, 'result');
    }
    
    // 提取限值信息 - 根据 XML 文档，对应 ACC_LOW 和 ACC_HIGH 元素
    let lowerLimit = '';
    let upperLimit = '';
    
    // 从 ACC_LOW 和 ACC_HIGH 元素获取限值
    lowerLimit = getElementText(element, 'ACC_LOW');
    upperLimit = getElementText(element, 'ACC_HIGH');
    
    // 如果没有找到，尝试其他可能的元素和属性
    if (!lowerLimit) {
      // 尝试 LIMIT 元素
      const limitElement = element.querySelector('LIMIT');
      if (limitElement) {
        lowerLimit = getElementAttr(limitElement, 'LOW') || getElementText(limitElement, 'LOW');
        upperLimit = upperLimit || getElementAttr(limitElement, 'HIGH') || getElementText(limitElement, 'HIGH');
      }
    }
    
    // 如果还是没有找到，尝试从 RESULT 元素获取 LIMIT_SEQ 属性
    if (!lowerLimit && resultElement) {
      const limitSeq = getElementAttr(resultElement, 'LIMIT_SEQ');
      if (limitSeq) {
        lowerLimit = `LIMIT_SEQ:${limitSeq}`;
      }
    }
    
    // 调试输出限值信息
    if (lowerLimit || upperLimit) {
      console.log(`测量 '${getElementText(element, 'ID')}' 的限值: 下限=${lowerLimit}, 上限=${upperLimit}`);
    }
    
    // 提取测试时间
    let testTime = getElementText(element, 'TEST_TIME');
    if (!testTime) {
      // 如果没有专门的测试时间元素，尝试从属性获取
      testTime = getElementAttr(element, 'time');
    }
    
    // 提取备注
    let comment = getElementText(element, 'COMMENT');
    if (!comment) {
      comment = getElementAttr(element, 'comment');
    }
    
    // 提取 QM 测量 ID
    let qmMeasId = getElementText(element, 'QM_MEAS_ID');
    if (!qmMeasId && resultElement) {
      // 如果没有专门的 QM_MEAS_ID 元素，可能在 RESULT 元素的属性中
      qmMeasId = getElementAttr(resultElement, 'qm_meas_id') || getElementAttr(element, 'qm_meas_id');
    }
    
    // 构建测量对象
    return {
      name: name,                                      // 测量名称
      step_type: getElementText(element, 'STEP_TYPE'),  // 测试类型
      measurement_id: getElementText(element, 'ID'),    // 测量 ID
      result_type: resultType,                         // 结果类型
      result_value: resultValue,                       // 结果值
      status: status,                                  // 状态
      unit_of_measure: unitOfMeasure,                  // 单位
      lower_limit: lowerLimit,                          // 下限
      upper_limit: upperLimit,                          // 上限
      test_time: testTime,                              // 测试时间
      comment: comment,                                 // 备注
      qm_meas_id: qmMeasId                              // QM 测量 ID
    };
  });
  
  // 返回完整的 JSON 结构
  return {
    filename_info,
    test_info,
    measurements
  };
}
