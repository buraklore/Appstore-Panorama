// Renders REAL Flutter screens to PNG (1170x2532, iPhone @3x) without a device.
// Copy to <your_app>/test/store_shots_test.dart, fill in the SCREENS section, then:
//   SHOTS=1 flutter test test/store_shots_test.dart      → PNGs in /tmp/shots
// Skipped in normal `flutter test` runs.
//
// Pitfalls this template already handles (each one silently ruins a store image):
//  1. google_fonts cannot download in tests → load the TTFs yourself (FontLoader) and
//     rebuild your theme with fontFamily: '<Family>' instead of GoogleFonts.*.
//  2. Material icons render as □ → load MaterialIcons-Regular.otf from the Flutter SDK.
//  3. Emoji render as tofu → load a color emoji font and add it as fontFamilyFallback.
//  4. Images in DecorationImage are NOT precached by find.byType(Image) → precache asset
//     folders explicitly (ASSET_DIRS).
//  5. Widgets that hit your backend in build/initState → add a preview constructor or
//     seed the repository cache (e.g. MyController.preview(fakeSnapshot)).
import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

final _skip = Platform.environment['SHOTS'] != '1';

// ---- CONFIGURE -------------------------------------------------------------------------
const FONT_FAMILY = 'Manrope';                     // your app font family
const FONT_FILES = [                               // static TTFs (instantiate variable fonts
  '/tmp/fonts/Manrope-Regular.ttf',                //  with fontTools if needed)
  '/tmp/fonts/Manrope-Bold.ttf',
  '/tmp/fonts/Manrope-ExtraBold.ttf',
];
const EMOJI_FONT = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'; // macOS: /System/Library/Fonts/Apple Color Emoji.ttc
const ASSET_DIRS = ['assets/images'];             // folders with images used as backgrounds

ThemeData shotTheme() {
  // TODO: copy your real ThemeData here, replacing GoogleFonts.* with FONT_FAMILY.
  final base = ThemeData(brightness: Brightness.dark, useMaterial3: true);
  return base.copyWith(
    textTheme: base.textTheme.apply(fontFamily: FONT_FAMILY, fontFamilyFallback: const ['Emoji']),
  );
}

final SCREENS = <String, Widget Function()>{
  // 'home': () => const HomeScreen(),
  // 'detail': () => DetailScreen(controller: DetailController.preview(fakeData)),
};
// -----------------------------------------------------------------------------------------

Future<void> _fonts(WidgetTester t) async {
  await t.runAsync(() async {
    Future<void> load(String family, List<String> files) async {
      final l = FontLoader(family);
      for (final f in files) {
        l.addFont(Future.value(ByteData.view(File(f).readAsBytesSync().buffer)));
      }
      await l.load();
    }
    await load(FONT_FAMILY, FONT_FILES);
    if (File(EMOJI_FONT).existsSync()) await load('Emoji', [EMOJI_FONT]);
    final sdk = File(Platform.resolvedExecutable).parent.parent.parent.parent.path; // …/flutter
    final icons = '$sdk/bin/cache/artifacts/material_fonts/MaterialIcons-Regular.otf';
    if (File(icons).existsSync()) await load('MaterialIcons', [icons]);
  });
}

Future<void> _shot(WidgetTester t, String name, Widget screen) async {
  t.view.physicalSize = const Size(1170, 2532);
  t.view.devicePixelRatio = 3;
  t.view.padding = const FakeViewPadding(top: 141, bottom: 102); // safe areas
  t.view.viewPadding = const FakeViewPadding(top: 141, bottom: 102);
  addTearDown(t.view.reset);
  final key = GlobalKey();
  await t.pumpWidget(RepaintBoundary(
    key: key,
    child: MaterialApp(debugShowCheckedModeBanner: false, theme: shotTheme(), home: screen),
  ));
  await t.pump(const Duration(milliseconds: 300));
  await t.runAsync(() async {
    for (final e in find.byType(Image).evaluate()) {
      await precacheImage((e.widget as Image).image, e);
    }
    final ctx = find.byType(MaterialApp).evaluate().first;
    for (final dir in ASSET_DIRS) {
      if (!Directory(dir).existsSync()) continue;
      for (final f in Directory(dir).listSync(recursive: true).whereType<File>()) {
        if (RegExp(r'\.(png|jpe?g|webp)$').hasMatch(f.path)) {
          await precacheImage(AssetImage(f.path), ctx);
        }
      }
    }
  });
  for (var i = 0; i < 10; i++) {
    await t.pump(const Duration(milliseconds: 300));
  }
  final b = key.currentContext!.findRenderObject()! as RenderRepaintBoundary;
  final bytes = await t.runAsync(() async {
    final img = await b.toImage(pixelRatio: 3);
    return (await img.toByteData(format: ui.ImageByteFormat.png))!.buffer.asUint8List();
  });
  Directory('/tmp/shots').createSync(recursive: true);
  File('/tmp/shots/$name.png').writeAsBytesSync(bytes!);
}

void main() {
  for (final e in SCREENS.entries) {
    testWidgets('shot ${e.key}', skip: _skip, (t) async {
      await _fonts(t);
      await _shot(t, e.key, e.value());
    });
  }
}
