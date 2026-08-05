import { StyleProp, StyleSheet, Text, View, ViewStyle } from 'react-native';

import { colors } from '@/constants/theme';

type BrandMarkProps = {
  size?: number;
  style?: StyleProp<ViewStyle>;
};

export function BrandMark({ size = 56, style }: BrandMarkProps) {
  return (
    <View
      accessibilityLabel="DigitalLife"
      style={[
        styles.mark,
        { borderRadius: size / 2, height: size, width: size },
        style,
      ]}>
      <View
        style={[
          styles.inner,
          {
            borderRadius: size / 2,
            height: size * 0.68,
            width: size * 0.68,
          },
        ]}>
        <Text allowFontScaling={false} style={[styles.letter, { fontSize: size * 0.36 }]}>
          D
        </Text>
      </View>
      <View style={[styles.companionDot, { height: size * 0.13, width: size * 0.13 }]} />
    </View>
  );
}

const styles = StyleSheet.create({
  mark: {
    alignItems: 'center',
    backgroundColor: colors.brand,
    justifyContent: 'center',
  },
  inner: {
    alignItems: 'center',
    backgroundColor: colors.surface,
    justifyContent: 'center',
  },
  letter: {
    color: colors.brand,
    fontWeight: '700',
  },
  companionDot: {
    backgroundColor: colors.surface,
    borderRadius: 999,
    bottom: '16%',
    position: 'absolute',
    right: '13%',
  },
});
