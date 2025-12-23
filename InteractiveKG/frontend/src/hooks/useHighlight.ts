

import { useState, useCallback } from 'react';
import { TestPhase } from '@/types/chatbot';

export interface HighlightConfig {
  targetId: string;
  duration?: number; 
  animationType?: 'pulse' | 'glow' | 'border' | 'background';
  intensity?: 'low' | 'medium' | 'high';
  color?: 'blue' | 'green' | 'orange' | 'purple' | 'teal' | 'red' | 'yellow'; 
}

export interface HighlightState {
  isHighlighted: boolean;
  targetId: string | null;
  config: HighlightConfig | null;
}


const PHASE_TO_TARGET_MAP: Record<TestPhase, string> = {
  
  [TestPhase.CASE1_INTRO]: '',
  [TestPhase.CASE1_LLM_RESPONSE]: '', 
  [TestPhase.CASE1_EXPLORE_GRAPH]: 'hierarchical-abstraction-panel',
  [TestPhase.CASE1_IDENTIFY_ERRORS]: 'property-panel', 
  [TestPhase.CASE1_EDIT_CORRECT]: 'property-panel',
  [TestPhase.CASE1_REQUERY_COMPARE]: 'enhanced-kgot-panel-retrieve',

  
  [TestPhase.CASE2_INTRO]: '',
  [TestPhase.CASE2_LLM_RESPONSE]: '', 
  [TestPhase.CASE2_EXPLORE_GRAPH]: 'hierarchical-abstraction-panel',
  [TestPhase.CASE2_IDENTIFY_ERRORS]: 'property-panel', 
  [TestPhase.CASE2_EDIT_CORRECT]: 'property-panel',
  [TestPhase.CASE2_REQUERY_COMPARE]: 'enhanced-kgot-panel-retrieve'
};


const PHASE_HIGHLIGHT_CONFIG: Record<TestPhase, Partial<HighlightConfig>> = {
  
  [TestPhase.CASE1_INTRO]: {},
  [TestPhase.CASE1_LLM_RESPONSE]: {},
  [TestPhase.CASE1_EXPLORE_GRAPH]: {
    animationType: 'pulse',
    intensity: 'high',
    duration: 5000,
    color: 'orange' 
  },
  [TestPhase.CASE1_IDENTIFY_ERRORS]: {
    animationType: 'border',
    intensity: 'high',
    duration: 5000,
    color: 'blue' 
  },
  [TestPhase.CASE1_EDIT_CORRECT]: {
    animationType: 'glow',
    intensity: 'medium',
    duration: 5000,
    color: 'purple' 
  },
  [TestPhase.CASE1_REQUERY_COMPARE]: {
    animationType: 'pulse',
    intensity: 'high',
    duration: 5000,
    color: 'yellow' 
  },

  
  [TestPhase.CASE2_INTRO]: {},
  [TestPhase.CASE2_LLM_RESPONSE]: {},
  [TestPhase.CASE2_EXPLORE_GRAPH]: {
    animationType: 'pulse',
    intensity: 'medium',
    duration: 5000,
    color: 'orange' 
  },
  [TestPhase.CASE2_IDENTIFY_ERRORS]: {
    animationType: 'border',
    intensity: 'high',
    duration: 5000,
    color: 'blue' 
  },
  [TestPhase.CASE2_EDIT_CORRECT]: {
    animationType: 'glow',
    intensity: 'medium',
    duration: 5000,
    color: 'purple' 
  },
  [TestPhase.CASE2_REQUERY_COMPARE]: {
    animationType: 'pulse',
    intensity: 'high',
    duration: 5000,
    color: 'yellow' 
  }
};


const ALL_HIGHLIGHT_TARGETS = [
  'enhanced-kgot-panel-solve',
  'enhanced-kgot-panel-retrieve',
  'hierarchical-abstraction-panel',
  'node-explanation-panel',
  'error-data-loader',
  'property-panel'
];

export const useHighlight = () => {
  const [highlightState, setHighlightState] = useState<HighlightState>({
    isHighlighted: false,
    targetId: null,
    config: null
  });

  
  const clearAllHighlights = useCallback(() => {
    ALL_HIGHLIGHT_TARGETS.forEach(targetId => {
      removeHighlightFromElement(targetId);
    });
  }, []);

  
  const highlightPhase = useCallback((phase: TestPhase) => {
    console.log(`🎯 高亮系统: 切换到阶段 ${phase}`);

    
    clearAllHighlights();

    const targetId = PHASE_TO_TARGET_MAP[phase];

    if (!targetId) {
      
      console.log(`🎯 高亮系统: 阶段 ${phase} 无需高亮，清除状态`);
      setHighlightState({
        isHighlighted: false,
        targetId: null,
        config: null
      });
      return;
    }

    const phaseConfig = PHASE_HIGHLIGHT_CONFIG[phase];
    const config: HighlightConfig = {
      targetId,
      duration: 4000,
      animationType: 'glow',
      intensity: 'medium',
      ...phaseConfig
    };

    console.log(`🎯 高亮系统: 高亮目标 ${targetId}，配置:`, config);

    setHighlightState({
      isHighlighted: true,
      targetId,
      config
    });

    
    applyHighlightToElement(config);

    
    if (config.duration && config.duration > 0) {
      setTimeout(() => {
        clearHighlight();
      }, config.duration);
    }
  }, [clearAllHighlights]);

  
  const clearHighlight = useCallback(() => {
    console.log(`🎯 高亮系统: 清除所有高亮效果`);

    
    clearAllHighlights();

    setHighlightState({
      isHighlighted: false,
      targetId: null,
      config: null
    });
  }, [clearAllHighlights]);

  
  const applyHighlightToElement = (config: HighlightConfig) => {
    const element = document.getElementById(config.targetId);
    if (!element) {
      console.warn(`🎯 高亮系统: 目标元素未找到 ${config.targetId}`);
      return;
    }

    console.log(`🎯 高亮系统: 应用高亮效果到 ${config.targetId}`);

    
    removeHighlightFromElement(config.targetId);

    
    const baseClassName = `highlight-${config.animationType}-${config.intensity}`;
    const colorClassName = config.color ? `highlight-${config.animationType}-${config.intensity}-${config.color}` : baseClassName;

    
    element.classList.add(colorClassName);

    console.log(`🎯 高亮系统: 添加CSS类 ${colorClassName} 到元素 ${config.targetId}`);

    
    element.scrollIntoView({
      behavior: 'smooth',
      block: 'center',
      inline: 'nearest'
    });
  };

  
  const removeHighlightFromElement = (targetId: string) => {
    const element = document.getElementById(targetId);
    if (!element) return;

    
    const colors = ['blue', 'green', 'orange', 'purple', 'teal', 'red', 'yellow'];
    const animations = ['pulse', 'glow', 'border', 'background'];
    const intensities = ['low', 'medium', 'high'];

    const highlightClasses = [];

    
    animations.forEach(animation => {
      intensities.forEach(intensity => {
        highlightClasses.push(`highlight-${animation}-${intensity}`);
        
        colors.forEach(color => {
          highlightClasses.push(`highlight-${animation}-${intensity}-${color}`);
        });
      });
    });

    
    highlightClasses.push('highlight-combo-attention', 'highlight-smart-solve', 'highlight-hierarchical', 'highlight-error-data');

    element.classList.remove(...highlightClasses);
  };

  
  const highlightElement = useCallback((targetId: string, config?: Partial<HighlightConfig>) => {
    console.log(`🎯 高亮系统: 手动高亮元素 ${targetId}`);

    
    clearAllHighlights();

    const fullConfig: HighlightConfig = {
      targetId,
      duration: 3000,
      animationType: 'glow',
      intensity: 'medium',
      ...config
    };

    setHighlightState({
      isHighlighted: true,
      targetId,
      config: fullConfig
    });

    applyHighlightToElement(fullConfig);

    if (fullConfig.duration && fullConfig.duration > 0) {
      setTimeout(() => {
        clearHighlight();
      }, fullConfig.duration);
    }
  }, [clearAllHighlights, clearHighlight]);

  
  const isElementHighlighted = useCallback((targetId: string) => {
    return highlightState.isHighlighted && highlightState.targetId === targetId;
  }, [highlightState]);

  return {
    highlightState,
    highlightPhase,
    highlightElement,
    clearHighlight,
    clearAllHighlights,
    isElementHighlighted
  };
};
