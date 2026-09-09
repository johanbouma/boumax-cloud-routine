import * as THREE from '../vendor/three.module.min.js';

const story = document.getElementById('atelierStory');
const stage = document.getElementById('atelierStage');
const canvas = document.getElementById('atelierCanvas');

const clamp = (value, min = 0, max = 1) => Math.min(max, Math.max(min, value));
const mix = (start, end, progress) => start + (end - start) * progress;
const smoothstep = (start, end, value) => {
  const progress = clamp((value - start) / Math.max(.0001, end - start));
  return progress * progress * (3 - 2 * progress);
};
const getScrollProgress = () => {
  const rect = story.getBoundingClientRect();
  return clamp(-rect.top / Math.max(1, rect.height - stage.clientHeight));
};
const phaseName = (progress) => {
  if (progress < .16) return 'result';
  if (progress < .43) return 'reveal';
  if (progress < .72) return 'system';
  if (progress < .9) return 'resolve';
  return 'result';
};

const roundedShape = (width, height, radius) => {
  const x = -width / 2;
  const y = -height / 2;
  const shape = new THREE.Shape();
  shape.moveTo(x + radius, y);
  shape.lineTo(x + width - radius, y);
  shape.quadraticCurveTo(x + width, y, x + width, y + radius);
  shape.lineTo(x + width, y + height - radius);
  shape.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
  shape.lineTo(x + radius, y + height);
  shape.quadraticCurveTo(x, y + height, x, y + height - radius);
  shape.lineTo(x, y + radius);
  shape.quadraticCurveTo(x, y, x + radius, y);
  return shape;
};

const makePanel = (width, height, depth, radius, material, bevel = .018) => {
  const geometry = new THREE.ExtrudeGeometry(roundedShape(width, height, radius), {
    depth,
    bevelEnabled: true,
    bevelSegments: 4,
    steps: 1,
    bevelSize: Math.min(radius * .1, bevel),
    bevelThickness: Math.min(depth * .12, bevel),
    curveSegments: 18,
  });
  geometry.center();
  return new THREE.Mesh(geometry, material);
};

const makeCanvasTexture = (draw, width = 2048, height = 1366) => {
  const surface = document.createElement('canvas');
  surface.width = width;
  surface.height = height;
  const context = surface.getContext('2d');
  draw(context, width, height);
  const texture = new THREE.CanvasTexture(surface);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.minFilter = THREE.LinearMipmapLinearFilter;
  texture.magFilter = THREE.LinearFilter;
  texture.generateMipmaps = true;
  return texture;
};

const makeSystemTexture = () => makeCanvasTexture((context, width, height) => {
  const gradient = context.createLinearGradient(0, 0, width, height);
  gradient.addColorStop(0, '#08152e');
  gradient.addColorStop(.56, '#0b1d43');
  gradient.addColorStop(1, '#071128');
  context.fillStyle = gradient;
  context.fillRect(0, 0, width, height);

  context.strokeStyle = 'rgba(133, 160, 218, .09)';
  context.lineWidth = 2;
  for (let x = 100; x < width; x += 130) {
    context.beginPath();
    context.moveTo(x, 0);
    context.lineTo(x, height);
    context.stroke();
  }
  for (let y = 96; y < height; y += 128) {
    context.beginPath();
    context.moveTo(0, y);
    context.lineTo(width, y);
    context.stroke();
  }

  context.fillStyle = 'rgba(220, 230, 249, .55)';
  context.font = '650 48px Outfit, sans-serif';
  context.letterSpacing = '9px';
  context.fillText('HET SYSTEEM ERACHTER', 150, 170);

  const nodes = [360, width / 2, width - 360];
  const labels = ['AANVRAAG', 'OFFERTE', 'OPVOLGING'];
  const line = context.createLinearGradient(nodes[0], 0, nodes[2], 0);
  line.addColorStop(0, 'rgba(90, 132, 255, .35)');
  line.addColorStop(.5, '#3970ff');
  line.addColorStop(1, 'rgba(90, 132, 255, .35)');
  context.strokeStyle = line;
  context.lineWidth = 10;
  context.beginPath();
  context.moveTo(nodes[0], height * .54);
  context.bezierCurveTo(width * .38, height * .43, width * .62, height * .65, nodes[2], height * .54);
  context.stroke();

  nodes.forEach((x, index) => {
    const y = height * .54;
    context.fillStyle = '#0a1835';
    context.strokeStyle = index === 1 ? '#dce7ff' : '#4c79f4';
    context.lineWidth = index === 1 ? 10 : 7;
    context.beginPath();
    context.arc(x, y, index === 1 ? 74 : 58, 0, Math.PI * 2);
    context.fill();
    context.stroke();
    context.fillStyle = index === 1 ? '#f4f7ff' : '#aebfe5';
    context.font = '700 39px Outfit, sans-serif';
    context.textAlign = 'center';
    context.letterSpacing = '5px';
    context.fillText(labels[index], x, y + 155);
  });

  context.textAlign = 'left';
  context.fillStyle = 'rgba(220, 230, 249, .42)';
  context.font = '500 34px Outfit, sans-serif';
  context.letterSpacing = '1px';
  context.fillText('Eén rustige route van eerste contact tot opvolging.', 150, height - 145);
});

const makeStructureTexture = () => makeCanvasTexture((context, width, height) => {
  const gradient = context.createLinearGradient(0, 0, width, height);
  gradient.addColorStop(0, '#eef1f6');
  gradient.addColorStop(.52, '#c7d0df');
  gradient.addColorStop(1, '#a2aec4');
  context.fillStyle = gradient;
  context.fillRect(0, 0, width, height);
  context.fillStyle = 'rgba(255, 255, 255, .22)';
  context.beginPath();
  context.arc(width * .78, height * .18, width * .23, 0, Math.PI * 2);
  context.fill();
  context.fillStyle = '#2864ff';
  context.fillRect(0, height * .69, width, 18);
  context.fillStyle = 'rgba(7, 18, 43, .72)';
  context.font = '700 48px Outfit, sans-serif';
  context.letterSpacing = '9px';
  context.fillText('DE OPBOUW', 150, 165);
  context.fillStyle = '#07122b';
  context.font = '700 146px Outfit, sans-serif';
  context.letterSpacing = '-5px';
  context.fillText('VAN VRAAG', 145, 430);
  context.fillText('NAAR VORM.', 145, 590);

  const points = [290, width / 2, width - 290];
  const labels = ['DOEL', 'VERHAAL', 'ACTIE'];
  context.strokeStyle = 'rgba(7, 18, 43, .38)';
  context.lineWidth = 5;
  context.beginPath();
  context.moveTo(points[0], height * .79);
  context.lineTo(points[2], height * .79);
  context.stroke();
  points.forEach((x, index) => {
    context.fillStyle = index === 1 ? '#2864ff' : '#07122b';
    context.beginPath();
    context.arc(x, height * .79, index === 1 ? 24 : 17, 0, Math.PI * 2);
    context.fill();
    context.fillStyle = 'rgba(7, 18, 43, .7)';
    context.font = '700 35px Outfit, sans-serif';
    context.textAlign = 'center';
    context.letterSpacing = '5px';
    context.fillText(labels[index], x, height * .89);
  });
  context.textAlign = 'left';
  context.fillStyle = 'rgba(7, 18, 43, .52)';
  context.font = '500 31px Outfit, sans-serif';
  context.letterSpacing = '1px';
  context.fillText('Iedere laag krijgt één duidelijke functie.', 150, height - 70);
});

if (story && stage && canvas) {
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const setPhase = (phase) => { story.dataset.activePhase = phase; };

  if (reduceMotion) {
    setPhase('result');
    story.dataset.webgl = 'disabled';
  } else {
    try {
      const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, powerPreference: 'high-performance' });
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.08;
      renderer.setClearColor(0x050b18, 1);

      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0x050b18);
      scene.fog = new THREE.FogExp2(0x050b18, .012);
      const camera = new THREE.PerspectiveCamera(31, 1, .1, 100);
      const cameraTarget = new THREE.Vector3(3.8, -.08, 0);

      scene.add(new THREE.HemisphereLight(0xe9efff, 0x061027, 2.1));
      const keyLight = new THREE.DirectionalLight(0xfff4e4, 4.8);
      keyLight.position.set(-5, 8, 8);
      const rimLight = new THREE.DirectionalLight(0x3c70ff, 6.2);
      rimLight.position.set(9, 3, 5);
      scene.add(keyLight, rimLight);

      const rig = new THREE.Group();
      scene.add(rig);

      const backMaterial = new THREE.MeshPhysicalMaterial({
        color: 0x111d36,
        metalness: .62,
        roughness: .23,
        clearcoat: .82,
        clearcoatRoughness: .22,
      });
      const backPlate = makePanel(11.12, 7.58, .24, .24, backMaterial);
      backPlate.position.z = -.62;
      rig.add(backPlate);

      const systemLayer = new THREE.Group();
      const systemBody = makePanel(10.92, 7.34, .16, .19, new THREE.MeshPhysicalMaterial({
        color: 0x0b1834,
        metalness: .28,
        roughness: .3,
        clearcoat: .7,
        clearcoatRoughness: .25,
      }));
      const systemSkin = new THREE.Mesh(new THREE.PlaneGeometry(10.68, 7.1), new THREE.MeshBasicMaterial({
        map: makeSystemTexture(),
        toneMapped: false,
      }));
      systemSkin.position.z = .102;
      systemLayer.add(systemBody, systemSkin);
      systemLayer.position.z = -.35;
      rig.add(systemLayer);

      const nodeMaterial = new THREE.MeshStandardMaterial({
        color: 0xcbd9ff,
        emissive: 0x2864ff,
        emissiveIntensity: 2.2,
        metalness: .18,
        roughness: .25,
      });
      [-3.36, 0, 3.36].forEach((x, index) => {
        const node = new THREE.Mesh(new THREE.SphereGeometry(index === 1 ? .13 : .1, 32, 24), nodeMaterial.clone());
        node.position.set(x, -.24, .22);
        systemLayer.add(node);
      });
      const pulse = new THREE.Mesh(new THREE.SphereGeometry(.105, 32, 24), new THREE.MeshBasicMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: 0,
        depthWrite: false,
        toneMapped: false,
      }));
      pulse.position.set(-3.36, -.24, .29);
      systemLayer.add(pulse);

      const structureLayer = new THREE.Group();
      const structureBody = makePanel(10.98, 7.42, .13, .2, new THREE.MeshPhysicalMaterial({
        color: 0xc8d1df,
        metalness: .34,
        roughness: .3,
        transmission: .08,
        clearcoat: .78,
        clearcoatRoughness: .18,
        transparent: true,
        opacity: .96,
      }));
      const structureSkin = new THREE.Mesh(new THREE.PlaneGeometry(10.72, 7.15), new THREE.MeshBasicMaterial({
        map: makeStructureTexture(),
        transparent: true,
        opacity: .9,
        toneMapped: false,
      }));
      structureSkin.position.z = .087;
      structureLayer.add(structureBody, structureSkin);
      structureLayer.position.z = -.08;
      rig.add(structureLayer);

      const surfaceLayer = new THREE.Group();
      const frameMaterial = new THREE.MeshPhysicalMaterial({
        color: 0xd9dee8,
        metalness: .74,
        roughness: .2,
        clearcoat: 1,
        clearcoatRoughness: .16,
      });
      const surfaceFrame = makePanel(11.04, 7.5, .18, .22, frameMaterial);
      const cobaltEdge = makePanel(10.84, 7.3, .055, .17, new THREE.MeshBasicMaterial({ color: 0x2864ff, transparent: true, opacity: .84 }), .01);
      cobaltEdge.position.z = .1;
      const screenMaterial = new THREE.MeshBasicMaterial({ color: 0x111b31, toneMapped: false });
      const screen = new THREE.Mesh(new THREE.PlaneGeometry(10.62, 7.08), screenMaterial);
      screen.position.z = .142;
      surfaceLayer.add(surfaceFrame, cobaltEdge, screen);
      surfaceLayer.position.z = .2;
      rig.add(surfaceLayer);

      const glass = new THREE.Mesh(new THREE.PlaneGeometry(10.58, 7.04), new THREE.MeshPhysicalMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: .045,
        roughness: .08,
        metalness: 0,
        transmission: .25,
        clearcoat: 1,
        depthWrite: false,
      }));
      glass.position.z = .158;
      glass.renderOrder = 4;
      surfaceLayer.add(glass);

      const textureLoader = new THREE.TextureLoader();
      textureLoader.load(new URL('../assets/hero-atelier/premium-website-v2.webp', import.meta.url).href, (texture) => {
        texture.colorSpace = THREE.SRGBColorSpace;
        texture.anisotropy = Math.min(16, renderer.capabilities.getMaxAnisotropy());
        texture.minFilter = THREE.LinearMipmapLinearFilter;
        texture.magFilter = THREE.LinearFilter;
        screenMaterial.map = texture;
        screenMaterial.color.setHex(0xffffff);
        screenMaterial.needsUpdate = true;
      });

      let compactScene = stage.clientWidth < 760;
      let activePhase = '';
      let pointerTargetX = 0;
      let pointerTargetY = 0;
      let pointerX = 0;
      let pointerY = 0;

      const updateStory = (progress) => {
        const openIn = smoothstep(.13, .43, progress);
        const closeOut = smoothstep(.72, .94, progress);
        const openness = openIn * (1 - closeOut);
        const structureFocus = smoothstep(.14, .28, progress) * (1 - smoothstep(.38, .49, progress));
        const systemFocus = smoothstep(.4, .58, progress) * (1 - smoothstep(.7, .86, progress));
        const phase = phaseName(progress);
        if (phase !== activePhase) {
          activePhase = phase;
          setPhase(phase);
        }

        const copyDip = smoothstep(.2, .39, progress) * (1 - smoothstep(.76, .94, progress));
        story.style.setProperty('--atelier-copy-opacity', String(compactScene ? 1 - copyDip * .7 : 1 - copyDip * .55));

        surfaceLayer.position.set(
          mix(0, -1.55, openness) - structureFocus * .7 - systemFocus * .9,
          mix(.2, .38, openness) + structureFocus * .45 + systemFocus * .18,
          mix(.2, -.28, openness) - structureFocus * .72 - systemFocus * .62,
        );
        surfaceLayer.rotation.set(
          mix(0, -.018, openness),
          mix(0, -.13, openness) - structureFocus * .08 - systemFocus * .12,
          mix(0, .018, openness),
        );
        structureLayer.position.set(
          mix(0, -.05, openness) + structureFocus * .65 - systemFocus * .85,
          mix(0, .12, openness) - structureFocus * .35 + systemFocus * .28,
          mix(-.08, .05, openness) + structureFocus * 1.68 - systemFocus * .58,
        );
        structureLayer.rotation.set(0, mix(0, -.025, openness) + structureFocus * .08, mix(0, -.008, openness));
        systemLayer.position.set(
          mix(0, 1.4, openness) + systemFocus * .25,
          mix(0, -.22, openness),
          mix(-.35, -.72, openness) + systemFocus * 2.72,
        );
        systemLayer.rotation.set(mix(0, .018, openness), mix(0, .09, openness) + systemFocus * .035, mix(0, -.018, openness));
        backPlate.position.set(mix(0, .12, openness), mix(0, -.08, openness), mix(-.62, -1.46, openness));

        structureSkin.material.opacity = mix(.9, .72, systemFocus);
        pulse.position.x = mix(-3.36, 3.36, smoothstep(.43, .7, progress));
        pulse.material.opacity = systemFocus;
        pulse.visible = systemFocus > .01;
        systemLayer.children.slice(2, 5).forEach((node, index) => {
          const local = smoothstep(.43 + index * .065, .53 + index * .065, progress) * (1 - closeOut);
          node.scale.setScalar(mix(.74, 1.2, local));
          node.material.emissiveIntensity = mix(.35, 2.6, local);
        });

        const baseX = compactScene ? .86 : 4.18;
        const baseY = compactScene ? -4.22 : -.08;
        const baseScale = compactScene ? .6 : 1.055;
        const systemReframe = systemFocus * (compactScene ? .95 : 2.05);
        rig.position.set(baseX - systemReframe + pointerX * (compactScene ? 0 : .16), baseY + pointerY * (compactScene ? 0 : .1), mix(.1, -.22, openness));
        rig.scale.setScalar(baseScale * mix(1, compactScene ? .8 : .78, openness));
        rig.rotation.set(
          mix(-.025, -.055, openness) + pointerY * .012,
          mix(-.105, -.025, openness) + pointerX * .018,
          mix(-.014, .005, openness),
        );

        camera.position.set(compactScene ? .2 : mix(.15, .45, openness), compactScene ? .2 : mix(.42, .24, openness), mix(15.8, 18.25, openness));
        cameraTarget.set(compactScene ? 0 : mix(0, .22, openness), compactScene ? 0 : -.08, 0);
        camera.lookAt(cameraTarget);
        rimLight.intensity = mix(5.8, 7.4, systemFocus);
      };

      const resize = () => {
        const width = stage.clientWidth;
        const height = stage.clientHeight;
        compactScene = width < 760;
        renderer.setPixelRatio(Math.min(devicePixelRatio, compactScene ? 1.5 : 2));
        renderer.setSize(width, height, false);
        camera.aspect = width / Math.max(1, height);
        camera.fov = compactScene ? 43 : 31;
        camera.updateProjectionMatrix();
      };

      if (matchMedia('(hover: hover) and (pointer: fine)').matches) {
        stage.addEventListener('pointermove', (event) => {
          const rect = stage.getBoundingClientRect();
          pointerTargetX = clamp((event.clientX - rect.left) / rect.width * 2 - 1, -1, 1);
          pointerTargetY = clamp(1 - (event.clientY - rect.top) / rect.height * 2, -1, 1);
        }, { passive: true });
        stage.addEventListener('pointerleave', () => {
          pointerTargetX = 0;
          pointerTargetY = 0;
        }, { passive: true });
      }

      let visible = true;
      let frame = 0;
      let lastTime = performance.now();
      let targetProgress = getScrollProgress();
      let renderProgress = targetProgress;
      const render = (time) => {
        frame = 0;
        if (!visible) return;
        const elapsed = Math.min(.05, Math.max(.001, (time - lastTime) / 1000));
        lastTime = time;
        targetProgress = getScrollProgress();
        const progressAlpha = 1 - Math.exp(-elapsed / .058);
        const pointerAlpha = 1 - Math.exp(-elapsed / .42);
        renderProgress += (targetProgress - renderProgress) * progressAlpha;
        pointerX += (pointerTargetX - pointerX) * pointerAlpha;
        pointerY += (pointerTargetY - pointerY) * pointerAlpha;
        if (Math.abs(targetProgress - renderProgress) < .0003) renderProgress = targetProgress;
        updateStory(renderProgress);
        renderer.render(scene, camera);
        frame = requestAnimationFrame(render);
      };

      const visibilityObserver = new IntersectionObserver(([entry]) => {
        visible = entry.isIntersecting;
        if (visible && !frame) {
          lastTime = performance.now();
          frame = requestAnimationFrame(render);
        } else if (!visible && frame) {
          cancelAnimationFrame(frame);
          frame = 0;
        }
      }, { rootMargin: '20% 0px' });

      resize();
      updateStory(renderProgress);
      visibilityObserver.observe(story);
      addEventListener('resize', resize, { passive: true });
      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState !== 'visible') return;
        renderProgress = getScrollProgress();
        lastTime = performance.now();
      });
      canvas.addEventListener('webglcontextlost', (event) => {
        event.preventDefault();
        story.classList.remove('is-webgl');
        story.dataset.webgl = 'failed';
      });
      story.classList.add('is-webgl');
      story.dataset.webgl = 'ready';
      frame = requestAnimationFrame(render);
    } catch (error) {
      story.dataset.webgl = 'failed';
      story.classList.remove('is-webgl');
      console.error('Het Levende Systeem kon niet worden gestart.', error);
    }
  }
}
